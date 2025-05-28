from agents.llm.llms.chatgpt import ChatGPT


def create_instance(name, params):
    if name == ChatGPT.name:
        llm = ChatGPT(params)
    else:
        llm = ChatGPT(params)
        
    return llm
