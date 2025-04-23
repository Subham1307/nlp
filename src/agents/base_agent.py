from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the agent's main task"""
        pass
    
    def log(self, message):
        """Log a message with the agent's name"""
        print(f"[{self.name}] {message}") 