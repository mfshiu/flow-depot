from agentflow.core.agent import Agent

import logging
from agents import get_logger
logger:logging.Logger = get_logger()



class MokeAgent(Agent):
    def __init__(self, name, agent_config):
        logger.debug(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
