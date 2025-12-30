# Параллельные вызовы инструментов

## Проблема

Агент делает много последовательных шагов:
- Step 1: vkusvill_products_search
- Step 2: vkusvill_product_details (id=1)
- Step 3: vkusvill_product_details (id=2)
- Step 4: vkusvill_product_details (id=3)
- ...

**Это медленно!** Можно вызвать все `vkusvill_product_details` параллельно.

## Решение 1: Parallel Tool Calls в OpenAI API

OpenAI поддерживает параллельные вызовы инструментов:

```python
# LLM может вернуть несколько tool_calls одновременно
response = {
    "tool_calls": [
        {"id": "call_1", "function": {"name": "vkusvill_product_details", "arguments": '{"id": 1}'}},
        {"id": "call_2", "function": {"name": "vkusvill_product_details", "arguments": '{"id": 2}'}},
        {"id": "call_3", "function": {"name": "vkusvill_product_details", "arguments": '{"id": 3}'}},
    ]
}
```

### Изменения в base_agent.py:

```python
async def _select_action_phase(self, reasoning=None) -> list[BaseTool]:
    """Return LIST of tools instead of single tool"""
    async with self.openai_client.chat.completions.stream(...) as stream:
        async for event in stream:
            if event.type == "chunk":
                self.streaming_generator.add_chunk(event.chunk)
    
    completion = await stream.get_final_completion()
    tool_calls = completion.choices[0].message.tool_calls
    
    # Parse ALL tool calls
    tools = []
    for tc in tool_calls:
        tool = tc.function.parsed_arguments
        tools.append(tool)
    
    return tools  # List of tools!

async def _action_phase(self, tools: list[BaseTool]) -> list[str]:
    """Execute tools in PARALLEL"""
    tasks = [tool(self._context, self.config) for tool in tools]
    results = await asyncio.gather(*tasks)  # Parallel execution!
    return results
```

### Изменения в execute():

```python
async def execute(self):
    while self._context.iteration < self.config.execution.max_iterations:
        reasoning = await self._reasoning_phase()
        
        # Get LIST of tools
        tools = await self._select_action_phase(reasoning)
        
        # Execute in PARALLEL
        results = await self._action_phase(tools)
        
        # Add all results to conversation
        for i, (tool, result) in enumerate(zip(tools, results)):
            self.conversation.append({
                "role": "tool",
                "content": result,
                "tool_call_id": f"{self._context.iteration}-action-{i}"
            })
        
        # Check if any tool is FinalAnswerTool
        if any(isinstance(t, FinalAnswerTool) for t in tools):
            break
```

## Решение 2: Prompt Engineering

Можно улучшить промпт, чтобы агент делал меньше шагов:

```yaml
system_prompt_str: |
  Ты - помощник по покупкам во ВкусВилл.
  
  ВАЖНО: Оптимизируй количество шагов!
  
  Стратегия работы:
  1. Используй vkusvill_products_search для поиска
  2. Выбери 3-5 лучших товаров из результатов поиска
  3. СРАЗУ создай корзину с vkusvill_cart_link_create (используй xml_id из поиска)
  4. Используй vkusvill_product_details ТОЛЬКО если пользователь просит детали
  
  НЕ НУЖНО:
  - Получать детали каждого товара, если пользователь не просил
  - Делать лишние запросы
  
  Результаты поиска уже содержат: название, цену, рейтинг, фото.
  Этого достаточно для создания корзины!
```

## Решение 3: Batch Tool (новый инструмент)

Создать специальный инструмент для пакетных запросов:

```python
class VkusvillBatchDetailsТool(BaseTool):
    """Get details for multiple products at once"""
    
    product_ids: list[int]
    
    async def __call__(self, context, config):
        # Call vkusvill_product_details for each ID in parallel
        tasks = [
            self._client.call_tool("vkusvill_product_details", {"id": pid})
            for pid in self.product_ids
        ]
        results = await asyncio.gather(*tasks)
        return json.dumps(results)
```

## Рекомендация

### Краткосрочно (быстро):
✅ **Решение 2**: Улучшить промпт - агент будет делать меньше шагов

### Среднесрочно:
✅ **Решение 1**: Реализовать параллельные вызовы в base_agent.py

### Долгосрочно:
✅ **Решение 3**: Создать batch-инструменты для популярных операций

## Текущий результат

Агент **РАБОТАЕТ** и создал корзину! 🎉

```
Корзина: https://vkusvill.ru/?share_basket=909445772

Товары:
1. Тартин пшеничный - 135 руб. (4.8★)
2. Багет Цельнозерновой - 173 руб. (4.8★)
3. Хлеб Коломенское Ржаной - 88 руб. (4.9★)
```

Просто делает это за 12 шагов вместо 3-4 возможных.

