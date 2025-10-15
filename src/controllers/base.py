from abc import ABC, abstractmethod

class Controller(ABC):
    """Base class for all game controllers (keyboard, vision, etc.)"""
    
    @abstractmethod
    def process_input(self):
        """Process input and return the current control state
        
        Returns:
            dict: A dictionary containing the current state of controls
                 {
                     1: {"movement": "none|left|right", "jump": "ready|jumping", "kick": "ready|kicking"},
                     2: {"movement": "none|left|right", "jump": "ready|jumping", "kick": "ready|kicking"}
                 }
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources used by the controller"""
        pass
