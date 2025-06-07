from enum import Enum

class AgentTopics(str, Enum):
    FILE_UPLOAD = "File/Upload"
    LLM_PROMPT = "Prompt/LlmService"
    STT_CONTENT = "STT/Content"
