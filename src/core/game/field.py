import os
from ...graphics.graphics import Circle, Point, Image
from ..config import x, y, larg_t, alt_t

class Field:
    def __init__(self, window_width, window_height, window):
        """Initialize the field with goals and collision points
        
        Args:
            window_width: Width of the game window
            window_height: Height of the game window
            window: GraphWin window to draw on
        """
        self.window = window
        self.width = window_width
        self.height = window_height
        
        # Get absolute paths for assets
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(src_dir, 'assets', 'images')
        
        # Create background
        bg_path = os.path.join(images_dir, 'bg.gif')
        self.background = Image(Point(window_width / 2, window_height / 2), bg_path)
        self.background.draw(window)
        
        # Left goal with absolute path
        left_goal_path = os.path.join(images_dir, 'trave1.gif')
        self.left_goal = Image(Point(55, 450), left_goal_path)
        self.left_goal.draw(window)
        self.left_goal_collision = Circle(Point(105, 360), 5)
        self.left_goal_collision.setOutline("")
        self.left_goal_collision.setFill("")
        self.left_goal_collision.draw(window)
        
        # Right goal with absolute path
        right_goal_path = os.path.join(images_dir, 'trave2.gif')
        self.right_goal = Image(Point(window_width - 55, 450), right_goal_path)
        self.right_goal.draw(window)
        self.right_goal_collision = Circle(Point(window_width - 105, 360), 5)
        self.right_goal_collision.setOutline("")
        self.right_goal_collision.setFill("")
        self.right_goal_collision.draw(window)
        
        # Goal boundaries
        self.left_goal_bounds = {
            'x1': self.left_goal.getAnchor().getX() - larg_t,
            'x2': self.left_goal.getAnchor().getX() + larg_t,
            'y1': self.left_goal.getAnchor().getY() - alt_t,
            'y2': self.left_goal.getAnchor().getY() + alt_t
        }
        
        self.right_goal_bounds = {
            'x1': self.right_goal.getAnchor().getX() - larg_t,
            'x2': self.right_goal.getAnchor().getX() + larg_t,
            'y1': self.right_goal.getAnchor().getY() - alt_t,
            'y2': self.right_goal.getAnchor().getY() + alt_t
        }
        
    def check_goal(self, ball_x, ball_y, ball_radius):
        """Check if a goal has been scored
        
        Args:
            ball_x: Ball's x position
            ball_y: Ball's y position
            ball_radius: Ball's radius
            
        Returns:
            tuple: (bool, str) - (is_goal, side_scored)
                  side_scored can be "left" or "right" or None
        """
        # Check left goal - ball must be fully inside the goal area AND below crossbar
        if (self.left_goal_bounds['x1'] <= ball_x - ball_radius and 
            ball_x + ball_radius <= self.left_goal_bounds['x2'] and
            self.left_goal_bounds['y1'] <= ball_y + ball_radius and
            ball_y - ball_radius <= self.left_goal_bounds['y2']):
            # Only count as goal if ball is below the crossbar
            if ball_y + ball_radius > self.left_goal_bounds['y1'] + 20:  # Add offset for crossbar
                return True, "right"  # Right player scores when ball enters left goal
            
        # Check right goal - ball must be fully inside the goal area AND below crossbar
        if (self.right_goal_bounds['x1'] <= ball_x - ball_radius and 
            ball_x + ball_radius <= self.right_goal_bounds['x2'] and
            self.right_goal_bounds['y1'] <= ball_y + ball_radius and
            ball_y - ball_radius <= self.right_goal_bounds['y2']):
            # Only count as goal if ball is below the crossbar
            if ball_y + ball_radius > self.right_goal_bounds['y1'] + 20:  # Add offset for crossbar
                return True, "left"  # Left player scores when ball enters right goal
            
        return False, None
        
    def check_field_collision(self, ball_x, ball_y, ball_radius, ball_velx, ball_vely):
        """Check and handle ball collisions with field boundaries and goal posts
        
        Args:
            ball_x: Ball's x position
            ball_y: Ball's y position
            ball_radius: Ball's radius
            ball_velx: Ball's x velocity
            ball_vely: Ball's y velocity
            
        Returns:
            tuple: (new_velx, new_vely) - Updated velocities after collision
        """
        new_velx = ball_velx
        new_vely = ball_vely
        RESTITUTION = 1.2  # Increased bounce factor
        MIN_BOUNCE_SPEED = 8  # Minimum bounce speed to ensure ball returns to play
        
        # Field boundaries with strong bounce back
        if ball_x + ball_radius > self.width:
            if ball_velx > 0:
                new_velx = -max(abs(ball_velx) * RESTITUTION, MIN_BOUNCE_SPEED)
                # Add inward force
                new_velx -= 3
        if ball_x - ball_radius < 0:
            if ball_velx < 0:
                new_velx = max(abs(ball_velx) * RESTITUTION, MIN_BOUNCE_SPEED)
                # Add inward force
                new_velx += 3
        if ball_y - ball_radius < 0:
            if ball_vely < 0:
                new_vely = max(abs(ball_vely) * RESTITUTION, MIN_BOUNCE_SPEED)
                # Add downward force
                new_vely += 4
                
        # Goal post collisions with strong bounce back
        # Left goal collision
        if (self.left_goal_bounds['x1'] - ball_radius <= ball_x <= self.left_goal_bounds['x2'] + ball_radius and
            ball_y <= self.left_goal_bounds['y1'] + 20):  # Crossbar height
            if ball_y + ball_radius > self.left_goal_bounds['y1'] - 5:
                # Strong bounce with additional outward force
                new_vely = -max(abs(ball_vely) * RESTITUTION, MIN_BOUNCE_SPEED)
                # Add slight push towards field center
                if ball_x < self.width / 2:
                    new_velx += 3
                else:
                    new_velx -= 3
                    
        # Right goal collision
        if (self.right_goal_bounds['x1'] - ball_radius <= ball_x <= self.right_goal_bounds['x2'] + ball_radius and
            ball_y <= self.right_goal_bounds['y1'] + 20):  # Crossbar height
            if ball_y + ball_radius > self.right_goal_bounds['y1'] - 5:
                # Strong bounce with additional outward force
                new_vely = -max(abs(ball_vely) * RESTITUTION, MIN_BOUNCE_SPEED)
                # Add slight push towards field center
                if ball_x < self.width / 2:
                    new_velx += 3
                else:
                    new_velx -= 3
                
        return new_velx, new_vely
        
    def get_goal_collision_points(self):
        """Get the collision points for both goals"""
        return {
            'left': (self.left_goal_collision.getCenter().getX(),
                    self.left_goal_collision.getCenter().getY()),
            'right': (self.right_goal_collision.getCenter().getX(),
                     self.right_goal_collision.getCenter().getY())
        }
        
    def get_goal_boundaries(self):
        """Get the boundary coordinates for both goals"""
        return {
            'left': self.left_goal_bounds,
            'right': self.right_goal_bounds
        }
