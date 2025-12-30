import asyncio
import logging
import logging.config
import yaml

from sgr_agent_core import AgentFactory, GlobalConfig

# Load logging config from YAML
with open("logging_config.yaml", "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)

# Override root logger format for clean output
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))


async def main():
    config = GlobalConfig.from_yaml("config.yaml")
    config.definitions_from_yaml("agents.yaml")

    agent1 = await AgentFactory.create(
        agent_def=config.agents["vkusvill_shopping_agent"],
        task="Найди хлеб свежий",
    )

    print("\n" + "="*80)
    print("AGENT CONFIG:")
    print("="*80)
    print(agent1.config.model_dump_json(indent=2))
    print("\n" + "="*80)
    print("AGENT EXECUTION:")
    print("="*80 + "\n")
    
    result = await agent1.execute()
    
    print("\n" + "="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(result)
    print("="*80 + "\n")



if __name__ == "__main__":
    asyncio.run(main())