from .base import Controller

class KeyboardController(Controller):
    """Controller implementation for keyboard input"""
    
    def __init__(self, window):
        """Initialize keyboard controller
        
        Args:
            window: The game window that provides keyboard input
        """
        self.window = window
        
        # Initialize key states
        self.keys_pressed = set()
        
        # Bind key events
        self.window.master.bind("<KeyPress>", self._on_key_press)
        self.window.master.bind("<KeyRelease>", self._on_key_release)
        
        self.players = {
            1: {"movement": "none", "jump": "ready", "kick": "ready"},
            2: {"movement": "none", "jump": "ready", "kick": "ready"}
        }
        
        print("Keyboard controller initialized with direct key bindings")
    
    def _on_key_press(self, event):
        """Handle key press events"""
        key = event.keysym.lower()
        self.keys_pressed.add(key)
        print(f"Key pressed: {key}")  # Debug info
        
    def _on_key_release(self, event):
        """Handle key release events"""
        key = event.keysym.lower()
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
            
    def process_input(self):
        """Process keyboard input
        
        Player 1 controls: A/D (movement), W (jump), SPACE (kick)
        Player 2 controls: LEFT/RIGHT (movement), UP (jump), RETURN (kick)
        """
        # Reset movement states
        self.players[1]["movement"] = "none"
        self.players[2]["movement"] = "none"
        
        # Process currently pressed keys
        for key in self.keys_pressed:
            # Player 1 controls
            if key == "a":
                self.players[1]["movement"] = "left"
            elif key == "d":
                self.players[1]["movement"] = "right"
            elif key == "w" and self.players[1]["jump"] == "ready":
                self.players[1]["jump"] = "jumping"
            elif key == "space" and self.players[1]["kick"] == "ready":
                self.players[1]["kick"] = "kicking"
            
            # Player 2 controls
            elif key == "left":
                self.players[2]["movement"] = "left"
            elif key == "right":
                self.players[2]["movement"] = "right"
            elif key == "up" and self.players[2]["jump"] == "ready":
                self.players[2]["jump"] = "jumping"
            elif key == "return" and self.players[2]["kick"] == "ready":
                self.players[2]["kick"] = "kicking"
        
        # Reset action states if key is not pressed
        if "w" not in self.keys_pressed and self.players[1]["jump"] == "jumping":
            self.players[1]["jump"] = "ready"
        if "space" not in self.keys_pressed and self.players[1]["kick"] == "kicking":
            self.players[1]["kick"] = "ready"
        if "up" not in self.keys_pressed and self.players[2]["jump"] == "jumping":
            self.players[2]["jump"] = "ready"
        if "return" not in self.keys_pressed and self.players[2]["kick"] == "kicking":
            self.players[2]["kick"] = "ready"
        
        # Debug info
        if self.keys_pressed:
            print(f"Active keys: {self.keys_pressed}")
            print(f"Player states: {self.players}")
            
        return self.players
    
    def cleanup(self):
        """No cleanup needed for keyboard controller"""
        pass
