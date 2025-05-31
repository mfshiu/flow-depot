from agentflow.core.agent import Agent
from agentflow.core.parcel import TextParcel
from agents.llm.llms import create_instance as create_llm
from agents.llm.llms.base_llm import LlmInstance
from agents.topics import AgentTopics

import logging
from app_logger import init_logging
logger:logging.Logger = init_logging()



class LlmService(Agent):
    def __init__(self, name, agent_config):
        logger.info(f"name: {name}, agent_config: {agent_config}")
        super().__init__(name, agent_config)
        self.llm_params = agent_config['agent']


    def on_activate(self):
        self.llm:LlmInstance = create_llm(self.llm_params['llm'], self.llm_params)
        self.subscribe(AgentTopics.LLM_PROMPT, "str", self.handle_prompt)


    def handle_prompt(self, topic:str, pcl:TextParcel):
        params = pcl.content

        response = self.llm.generate_response(params)
        logger.debug(self.M(response))

        return {
            'response': response,
        }
