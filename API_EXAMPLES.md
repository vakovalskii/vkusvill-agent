# VkusVill Shopping Agent - API Examples

## 🚀 Запуск API

### Docker
```bash
docker-compose up -d
```

### Локально
```bash
python api.py
# или
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступен на: http://localhost:8000

Документация: http://localhost:8000/docs

## 📋 Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### 2. Root
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "VkusVill Shopping Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 3. List Agents
```bash
curl http://localhost:8000/agents
```

**Response:**
```json
{
  "agents": ["vkusvill_shopping_agent"],
  "default": "vkusvill_shopping_agent"
}
```

### 4. Execute Task
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди хлеб свежий"
  }'
```

**Response:**
```json
{
  "success": true,
  "result": "Вот что я нашел:\n\n1. Тартин пшеничный. Пекарня - 89.99₽, рейтинг 4.8\n2. Хлеб Бородинский - 65.99₽, рейтинг 4.7\n...\n\nСсылка на корзину: https://vkusvill.ru/?share_basket=123456",
  "agent_id": "vkusvill_shopping_agent_abc123",
  "error": null
}
```

## 🔍 Примеры задач

### Простой поиск
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди молоко"
  }'
```

### Поиск с сортировкой
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди хлеб, отсортируй по цене"
  }'
```

### Поиск с деталями
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди молоко и покажи состав"
  }'
```

### Создание корзины
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди хлеб, молоко и яйца, создай корзину"
  }'
```

### Сложный запрос
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Найди 3 самых популярных товара из категории молочные продукты и создай корзину"
  }'
```

## 🐍 Python Client

### Простой пример
```python
import requests

def search_products(task: str):
    response = requests.post(
        "http://localhost:8000/task",
        json={"task": task}
    )
    return response.json()

# Использование
result = search_products("Найди хлеб свежий")
print(result["result"])
```

### С обработкой ошибок
```python
import requests
from typing import Dict, Any

def execute_task(task: str, agent_name: str = "vkusvill_shopping_agent") -> Dict[str, Any]:
    """
    Выполнить задачу через VkusVill Shopping Agent API
    
    Args:
        task: Задача для агента
        agent_name: Имя агента (по умолчанию vkusvill_shopping_agent)
    
    Returns:
        Dict с результатом выполнения
    
    Raises:
        requests.HTTPError: Если запрос не удался
    """
    try:
        response = requests.post(
            "http://localhost:8000/task",
            json={
                "task": task,
                "agent_name": agent_name
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout"
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

# Использование
result = execute_task("Найди молоко")
if result["success"]:
    print("✅ Успешно!")
    print(result["result"])
else:
    print("❌ Ошибка:", result.get("error"))
```

### Асинхронный клиент
```python
import asyncio
import httpx

async def execute_task_async(task: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/task",
            json={"task": task},
            timeout=60.0
        )
        return response.json()

# Использование
async def main():
    result = await execute_task_async("Найди хлеб свежий")
    print(result["result"])

asyncio.run(main())
```

### Batch запросы
```python
import asyncio
import httpx

async def execute_tasks_batch(tasks: list[str]):
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[
            client.post(
                "http://localhost:8000/task",
                json={"task": task},
                timeout=60.0
            )
            for task in tasks
        ])
        return [r.json() for r in responses]

# Использование
async def main():
    tasks = [
        "Найди хлеб",
        "Найди молоко",
        "Найди яйца"
    ]
    results = await execute_tasks_batch(tasks)
    for result in results:
        print(result["result"])
        print("-" * 80)

asyncio.run(main())
```

## 🔧 Настройка

### Изменение порта
```bash
# Docker Compose
# Отредактируйте docker-compose.yml:
ports:
  - "9000:8000"  # Внешний порт 9000

# Локально
uvicorn api:app --host 0.0.0.0 --port 9000
```

### Добавление CORS
Отредактируйте `api.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Аутентификация
Добавьте API ключ в `api.py`:
```python
from fastapi import Header, HTTPException

async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.post("/task", dependencies=[Depends(verify_token)])
async def execute_task(request: TaskRequest):
    # ...
```

## 📊 Мониторинг

### Логи
```bash
# Docker
docker-compose logs -f

# Локально
tail -f logs/sgr_agent_core.log
```

### Метрики
```bash
# Количество запросов
curl http://localhost:8000/metrics  # Если добавить prometheus
```

## 🐛 Отладка

### Проверка доступности
```bash
curl -v http://localhost:8000/health
```

### Просмотр логов контейнера
```bash
docker-compose logs -f vkusvill-agent
```

### Вход в контейнер
```bash
docker-compose exec vkusvill-agent bash
```

### Тестирование локально
```bash
# Запустить в режиме разработки с автоперезагрузкой
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## 📝 Swagger UI

Интерактивная документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Здесь можно:
- Просмотреть все endpoints
- Протестировать API прямо в браузере
- Посмотреть схемы запросов/ответов
- Скачать OpenAPI спецификацию

