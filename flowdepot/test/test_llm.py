# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import unittest
import yaml

import logging
from flowdepot.app_logger import init_logging
logger:logging.Logger = init_logging()

from agentflow.core.agent import Agent
from agentflow.core.parcel import TextParcel, Parcel
from agents.topics import AgentTopics


config_path = os.path.join(os.getcwd(), 'config', 'system.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    system_config = yaml.safe_load(f) or {}



class TestAgent(unittest.TestCase):
    result_question = ''
    
    class ValidationAgent(Agent):
        def __init__(self):
            super().__init__(name='main', agent_config=system_config)


        def on_activate(self):
            self.subscribe('llm_response')
            
            messages = "Please create a question about the water cycle."
            pcl = TextParcel(messages, 'llm_response')
            self.publish(AgentTopics.LLM_PROMPT , pcl)


        def on_message(self, topic:str, pcl:Parcel):
            llm_resp:dict = pcl.content or {}
            logger.debug(self.M(f"topic: {topic}, llm_resp: {llm_resp}"))

            TestAgent.result_question = llm_resp.get('response', '')


    def setUp(self):
        self.validation_agent = TestAgent.ValidationAgent()
        self.validation_agent.start_thread()


    def _do_test_1(self):
        self.assertTrue(TestAgent.result_question)


    def test_1(self):
        time.sleep(3)

        try:
            self._do_test_1()
        except Exception as ex:
            logger.exception(ex)
            self.assertTrue(False)


    def tearDown(self):
        self.validation_agent.terminate()



if __name__ == '__main__':
    unittest.main()
