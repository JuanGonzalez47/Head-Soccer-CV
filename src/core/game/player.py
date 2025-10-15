from ...graphics.graphics import Circle, Point, Image
from ..config import raio, raio_cabeca, x, chao

class Player:
    def __init__(self, x, y, is_left_player, window):
        """Initialize a player with their body parts and sprites
        
        Args:
            x: Initial x position
            y: Initial y position
            is_left_player: True if this is the left player, False for right
            window: GraphWin window to draw on
        """
        # Constants for collision detection
        self.COLLISION_RADIUS = 40  # Match the game's collision radius
        self.is_left_player = is_left_player
        self.window = window
        
        # Create collision circles
        self.head = Circle(Point(x, y - 12), raio_cabeca)
        self.head.setOutline("")
        self.head.setFill("")
        self.head.draw(window)
        
        self.foot = Circle(Point(x, y + 26), raio)
        self.foot.setOutline("")
        self.foot.setFill("")
        self.foot.draw(window)
        
        # Create sprite with correct path
        import os
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(src_dir, "assets", "images")
        
        sprite_file = "LeftChar.gif" if is_left_player else "RightChar.gif"
        sprite_path = os.path.join(images_dir, sprite_file)
        self.sprite = Image(Point(x, y), sprite_path)
        self.sprite.draw(window)
        
        # State variables
        self.jumping = False
        self.jump_ready = True  # Track if player can jump again
        self.jump_count = 0
        self.kicking = False
        self.kick_count = 0
        
    def move(self, dx, dy):
        """Move the player by the given amounts while respecting field boundaries"""
        # Get current position
        head_x = self.head.getCenter().getX()
        
        # Check field boundaries before moving
        if dx < 0 and head_x - raio_cabeca + dx <= 0:
            # Don't move past left boundary
            dx = 0
        elif dx > 0 and head_x + raio_cabeca + dx >= x:
            # Don't move past right boundary
            dx = 0
            
        # Apply allowed movement
        self.head.move(dx, dy)
        self.foot.move(dx, dy)
        self.sprite.move(dx, dy)
        
    def set_position(self, x, y):
        """Set the player to a specific position and reset movement states"""
        # Move to new position
        current_x = self.sprite.getAnchor().getX()
        current_y = self.sprite.getAnchor().getY()
        self.move(x - current_x, y - current_y)
        
        # Reset all movement states
        self.jumping = False
        self.jump_ready = True
        self.jump_count = 0
        self.kicking = False
        self.kick_count = 0
        
    def start_jump(self):
        """Start jumping animation if ready"""
        if self.jump_ready and not self.jumping and not self.kicking:
            self.jumping = True
            self.jump_count = 0
            self.jump_ready = False  # Can't jump again until landing
            
    def update_jump(self):
        """Update jump animation state using original game physics"""
        # When jumping, apply upward force first then gravity
        if self.jumping and not self.kicking:
            if self.jump_count < 12:
                # Going up
                self.move(0, -8)
            elif self.jump_count < 24:
                # Coming down
                self.move(0, 8)
            
            self.jump_count += 1
            
            if self.jump_count >= 24:
                self.jumping = False
                self.jump_count = 0
                
        # Check if we're on ground to reset jump ability
        if self.foot.getCenter().getY() + raio >= chao - 5:  # Small threshold
            self.jump_ready = True
                
    def start_kick(self):
        """Start kicking animation"""
        if not self.kicking:
            self.kicking = True
            self.kick_count = 0
            
    def update_kick(self):
        """Update kick animation state"""
        if self.kicking:
            if self.kick_count // 1 == 0:
                self.foot.move(0, 8)
                # Update sprite
                self._update_sprite('kick1')
            if self.kick_count // 8 == 1:
                self.foot.move(2 if self.is_left_player else -2, -2)
                # Update sprite
                self._update_sprite('kick2')
                
            self.kick_count += 1
            if self.kick_count == 15:
                # Reset sprite
                self._update_sprite('')
                self.kick_count = 0
                self.foot.move(-14 if self.is_left_player else 14, 6)
                self.kicking = False
                
    def _update_sprite(self, action):
        """Update the player's sprite
        
        Args:
            action: Action name ('', 'kick1', 'kick2')
        """
        import os
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(src_dir, "assets", "images")
        
        self.sprite.undraw()
        prefix = "Left" if self.is_left_player else "Right"
        suffix = f"_{action}" if action else ""
        sprite_path = os.path.join(images_dir, f"{prefix}Char{suffix}.gif")
        
        self.sprite = Image(
            self.sprite.getAnchor(),
            sprite_path
        )
        self.sprite.draw(self.window)
        
    @property
    def head_position(self):
        """Get the head's position"""
        return (self.head.getCenter().getX(), self.head.getCenter().getY())
        
    @property
    def foot_position(self):
        """Get the foot's position"""
        return (self.foot.getCenter().getX(), self.foot.getCenter().getY())
        
    @property
    def sprite_position(self):
        """Get the sprite's position"""
        anchor = self.sprite.getAnchor()
        return (anchor.getX(), anchor.getY())
