from enum import Enum

class AgentTopics(str, Enum):
    LLM_PROMPT = "Prompt/LlmService"
    FILE_UPLOAD = "File/Upload"
