from .base import Controller

class KeyboardController(Controller):
    """Controller implementation for keyboard input"""
    
    def __init__(self, window):
        """Initialize keyboard controller
        
        Args:
            window: The game window that provides keyboard input
        """
        self.window = window
        self.players = {
            1: {"movement": "none", "jump": "ready", "kick": "ready"},
            2: {"movement": "none", "jump": "ready", "kick": "ready"}
        }
    
    def process_input(self):
        """Process keyboard input
        
        Player 1 controls: A/D (movement), W (jump), SPACE (kick)
        Player 2 controls: LEFT/RIGHT (movement), UP (jump), RETURN (kick)
        """
        # Get all pending keyboard events
        keys = self.window.checkKey_Buffer() if hasattr(self.window, 'checkKey_Buffer') else [self.window.checkKey()]
        
        # Reset movement states
        self.players[1]["movement"] = "none"
        self.players[2]["movement"] = "none"
        
        # Process each key
        for key in keys:
            if not key:
                continue
                
            # Player 1 controls
            if key == "a":
                self.players[1]["movement"] = "left"
            elif key == "d":
                self.players[1]["movement"] = "right"
            elif key == "w":
                self.players[1]["jump"] = "jumping"
            elif key == "space":
                self.players[1]["kick"] = "kicking"
                
            # Player 2 controls
            elif key == "Left":
                self.players[2]["movement"] = "left"
            elif key == "Right":
                self.players[2]["movement"] = "right"
            elif key == "Up":
                self.players[2]["jump"] = "jumping"
            elif key == "Return":
                self.players[2]["kick"] = "kicking"
        
        return self.players
    
    def cleanup(self):
        """No cleanup needed for keyboard controller"""
        pass
