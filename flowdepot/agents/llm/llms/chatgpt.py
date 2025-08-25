from openai import OpenAI
import json
import yaml

import logging, os

from agents.llm.llms.base_llm import LlmInstance
logger:logging.Logger = logging.getLogger(os.getenv('LOGGER_NAME'))


class ChatGPT(LlmInstance):
    name = "ChatGPT"
    
    default_params = {
        'model': 'gpt-4o-mini',
        # 'response_format': 'text',  # 'text' or dict (function-calling format)
        'temperature': 0,
        'streaming': False,
        'openai_api_key': "",
    }


    def __init__(self, params: dict):
        super().__init__(name=ChatGPT.name)
        
        self.prompt_params = ChatGPT.default_params.copy()
        self.prompt_params.update(params)

        self.model = self.prompt_params['model']
        self.temperature = self.prompt_params['temperature']
        self.streaming = self.prompt_params['streaming']
        self.api_key = self.prompt_params['openai_api_key']
        self.response_format = self.prompt_params.get('response_format', None)

        self.client = OpenAI(api_key=self.api_key)


    def generate_response(self, prompt_params):
        """
        Generate a response from an OpenAI chat model.

        Args:
            params (str | list[dict] | dict): 
                - If str: treated as a single prompt.
                - If list of dicts: treated as a messages array.
                - If dict: should include a 'messages' key and optionally other settings 
                like 'model', 'temperature', etc.

        Returns:
            str: The generated response text (streamed or full depending on settings).
        """
        if isinstance(prompt_params, str):
            # prompt text only
            messages = [{"role": "user", "content": prompt_params}]
            params = {'messages': messages}
        elif isinstance(prompt_params, list) and isinstance(prompt_params[0], dict):
            # messages list only
            messages = prompt_params
            params = {'messages': messages}
        elif isinstance(prompt_params, dict):
            # must contains 'messages' key
            params = self.prompt_params.copy()
            params.update(prompt_params)
            messages = params['messages']
        else:
            raise ValueError("Invalid input.")

        kwargs = {
            "model": params.get('model', self.model),
            "messages": messages,
            "temperature": params.get('temperature', self.temperature),
            "stream": params.get('streaming', self.streaming),
        }
        response_format = params.get('response_format', self.response_format)
        if response_format:
            kwargs['response_format'] = response_format

        response = self.client.chat.completions.create(**kwargs)

        if self.streaming:
            result = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    result += chunk.choices[0].delta.content
            return result
        else:
            choice = response.choices[0]
            return choice.message.content


if __name__ == '__main__':
    prompt_text = "Please create a question about the water cycle."
    
    messages=[
        {"role": "system", "content": "You are a helpful exam question generator. Please provide your response in JSON format."},
        {"role": "user", "content": f"{prompt_text}\nPlease provide your response in JSON format."}
    ]
    
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "generate_question",
            "schema": {
                "type": "object",
                "properties": {
                    "stem": {"type": "string"},
                    "option_A": {"type": "string"},
                    "option_B": {"type": "string"},
                    "option_C": {"type": "string"},
                    "option_D": {"type": "string"},
                    "answer": {"type": "string"},
                },
                "required": [
                    "stem",
                    "option_A",
                    "option_B",
                    "option_C",
                    "option_D",
                    "answer"
                ],
                "additionalProperties": False
            }
        }
    }
    
    config_path = os.path.join(os.getcwd(), 'config', 'system.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        params = (yaml.safe_load(f) or {}).get('llm', {})

    llm = ChatGPT(params)
    messages = "Please create a question about the water cycle."
    result = llm.generate_response(messages)
    # params['messages'] = messages
    # result = llm.generate_response(params)
    print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
