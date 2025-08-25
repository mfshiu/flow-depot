from abc import ABC, abstractmethod



class LlmInstance(ABC):
    def __init__(self, name:str):
        self.name = name
        
    
    @abstractmethod
    def generate_response(self, params):
        pass
