"""
VkusVill Shopping Agent - FastAPI Server
"""
import asyncio
import logging
import logging.config
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from sgr_agent_core import AgentFactory, GlobalConfig

# Load logging config
with open("logging_config.yaml", "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)

# Override root logger format for clean output
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VkusVill Shopping Agent API",
    description="AI-агент для поиска товаров и создания корзины покупок в магазине ВкусВилл",
    version="1.0.0",
)

# Load agent configuration
config = GlobalConfig.from_yaml("config.yaml")
config.definitions_from_yaml("agents.yaml")


class TaskRequest(BaseModel):
    """Request model for agent task"""
    task: str = Field(..., description="Задача для агента (например: 'Найди хлеб свежий')")
    agent_name: str = Field(
        default="vkusvill_shopping_agent",
        description="Имя агента из agents.yaml"
    )


class TaskResponse(BaseModel):
    """Response model for agent task"""
    success: bool = Field(..., description="Успешно ли выполнена задача")
    result: str = Field(..., description="Результат выполнения агента")
    agent_id: str = Field(..., description="ID агента")
    error: Optional[str] = Field(None, description="Сообщение об ошибке (если есть)")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VkusVill Shopping Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Выполнить задачу агента
    
    Примеры задач:
    - "Найди хлеб свежий"
    - "Найди молоко и покажи состав"
    - "Найди хлеб, молоко и яйца, создай корзину"
    """
    try:
        logger.info(f"Received task: {request.task}")
        
        # Create agent
        agent = await AgentFactory.create(
            agent_def=config.agents[request.agent_name],
            task=request.task,
        )
        
        logger.info(f"Created agent: {agent.id}")
        
        # Execute task
        result = await agent.execute()
        
        logger.info(f"Task completed successfully: {agent.id}")
        
        return TaskResponse(
            success=True,
            result=result,
            agent_id=agent.id,
            error=None
        )
        
    except KeyError as e:
        logger.error(f"Agent not found: {request.agent_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{request.agent_name}' not found in agents.yaml"
        )
    
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing task: {str(e)}"
        )


@app.get("/agents")
async def list_agents():
    """Список доступных агентов"""
    return {
        "agents": list(config.agents.keys()),
        "default": "vkusvill_shopping_agent"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

