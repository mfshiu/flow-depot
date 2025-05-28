from enum import Enum, auto
import time

from agentflow.core.agent import Agent
from agentflow.core.parcel import TextParcel
from llms import create_instance as create_llm
from llms.base_llm import LlmInstance

import logging
from agents import LOGGER_NAME
logger:logging.Logger = logging.getLogger(LOGGER_NAME)



class LlmService(Agent):
    TOPIC_LLM_PROMPT = "Prompt/LlmService"
    
    
    def __init__(self, name, agent_config, llm_params):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.llm_params = llm_params


    def on_activate(self):
        self.llm:LlmInstance = create_llm(self.llm_params['llm'], self.llm_params)
        self.subscribe(LlmService.TOPIC_LLM_PROMPT, "str", self.handle_prompt)


    def handle_prompt(self, topic:str, pcl:TextParcel):
        params = pcl.content

        response = self.llm.generate_response(params)
        logger.debug(self.M(response))

        return {
            'response': response,
        }
