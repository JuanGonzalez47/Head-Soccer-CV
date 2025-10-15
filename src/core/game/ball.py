from ...graphics.graphics import Circle, Point, Image
from ..config import raio

class Ball:
    def __init__(self, x, y, window):
        """Initialize the ball with its collision circle and sprite
        
        Args:
            x: Initial x position
            y: Initial y position
            window: GraphWin window to draw on
        """
        self.collision_circle = Circle(Point(x, y), raio)
        self.collision_circle.setOutline("")
        self.collision_circle.setFill("")
        self.collision_circle.draw(window)
        
        # Get correct path for ball sprite
        import os
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(src_dir, "assets", "images")
        ball_path = os.path.join(images_dir, "ball.gif")
        
        self.sprite = Image(Point(x, y), ball_path)
        self.sprite.draw(window)
        
        self.velx = 0
        self.vely = 0
        self.window = window
        
    @property
    def x(self):
        """Current x position of the ball"""
        return self.collision_circle.getCenter().getX()
        
    @property
    def y(self):
        """Current y position of the ball"""
        return self.collision_circle.getCenter().getY()
        
    def move(self, dx, dy):
        """Move the ball by the given amounts"""
        self.collision_circle.move(dx, dy)
        self.sprite.move(dx, dy)
        
    def set_position(self, x, y):
        """Set the ball to a specific position"""
        current_x = self.x
        current_y = self.y
        self.move(x - current_x, y - current_y)
        
    def apply_physics(self, atrito, chao):
        """Apply physics calculations to the ball
        
        Args:
            atrito: Friction coefficient
            chao: Floor y-coordinate
        """
        # Apply gravity when ball is in air
        if self.y + raio < chao:
            # Apply gravity with increasing effect up to terminal velocity
            if self.vely < 12:  # Terminal velocity
                self.vely += 0.4  # Base gravity

            
        # Apply velocity
        self.move(2 * self.velx // 1, 2 * self.vely // 1)
        
        # Ground collision and friction
        if self.y + raio >= chao:
            # Enforce ground boundary and calculate bounce
            if self.y + raio > chao:
                # Move to ground surface
                self.move(0, chao - (self.y + raio))
                
                # Calculate bounce with more energy loss
                bounce_factor = min(0.6, max(0.3, abs(self.vely) / 25))  # Reducimos el factor de rebote
                if abs(self.vely) > 2:  # Only bounce if moving fast enough
                    self.vely = (self.vely * -bounce_factor) // 1
                else:
                    self.vely = 0  # Stop vertical movement
                    
                # Reduce horizontal speed more on impact
                self.velx = (self.velx * 0.6) // 1  # Mayor pérdida de velocidad horizontal
                
            if self.y + raio == chao:
                # Apply friction when ball is on ground
                if self.velx > 0:
                    self.velx -= atrito
                if self.velx < 0:
                    self.velx += atrito
                # Ensure velocity stops at zero
                if abs(self.velx) < atrito:
                    self.velx = 0
                    
    def reset(self, x, y):
        """Reset ball to initial position with no velocity"""
        self.set_position(x, y)
        self.velx = 0
        self.vely = 0
