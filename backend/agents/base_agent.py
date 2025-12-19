from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the electrolyte design system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process the input and return results."""
        pass
    
    def log_action(self, action: str, details: str = ""):
        """Log agent actions for traceability."""
        self.logger.info(f"[{self.name}] {action}: {details}")
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: list) -> bool:
        """Validate that required keys are present in input."""
        missing = [key for key in required_keys if key not in input_data]
        if missing:
            self.logger.warning(f"Missing required keys: {missing}")
            return False
        return True



