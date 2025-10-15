import os
import sys
import time
import math
from ...graphics.graphics import GraphWin, Point, Text, Image
from ..config import (
    x, y, raio, raio_cabeca, chao, vel, atrito,
    larg_t, alt_t, contador_gol1, contador_gol2
)
from .ball import Ball
from .field import Field
from .player import Player
from ...controllers.vision import VisionController
from ...controllers.keyboard import KeyboardController

class Game:
    def __init__(self):
        """Initialize the game window and all components"""
        # Create main window
        self.window = GraphWin("Head Soccer", x, y, False)
        
        # Initialize game state
        self.score = {"left": 0, "right": 0}
        self.is_goal = False
        
        # Initialize controllers
        self.setup_controllers()
        
        # Show intro screen
        self.show_intro()
        
        # Initialize game objects
        self.setup_game_objects()
        
        # Initialize score display
        self.setup_score_display()
        
    def setup_controllers(self):
        """Initialize game controllers (vision or keyboard)"""
        try:
            self.vision_controller = VisionController()
            self.controller = self.vision_controller
            self.use_vision = True
            print("Vision controller initialized successfully!")
        except Exception as e:
            print(f"Could not initialize vision controller: {e}")
            print("Falling back to keyboard controls")
            self.controller = KeyboardController(self.window)
            self.use_vision = False
            
    def show_intro(self):
        """Show and handle the intro screen"""
        # Load intro screen images
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        image_dir = os.path.join(src_dir, "assets", "images")
        
        intro = Image(Point(x / 2, y / 2), os.path.join(image_dir, "intro2.gif"))
        intro.draw(self.window)
        
        jogar = Image(Point(175, 500), os.path.join(image_dir, "jogar.gif"))
        jogar.draw(self.window)
        
        sair = Image(Point(425, 500), os.path.join(image_dir, "sair.gif"))
        sair.draw(self.window)
        
        # Wait for player input
        while True:
            enter = self.window.checkKey()
            check = self.window.checkMouse()
            
            if check is not None:
                check_x = check.getX()
                check_y = check.getY()
                if (470 <= check_y <= 530) and (75 <= check_x <= 275):
                    time.sleep(0.06)
                    break
                elif (470 <= check_y <= 530) and (325 <= check_x <= 525):
                    time.sleep(0.2)
                    if self.use_vision:
                        self.vision_controller.cleanup()
                    self.window.close()
                    sys.exit()
            else:
                if enter == "Return":
                    time.sleep(0.06)
                    break
            time.sleep(0.07)
            
        # Clear intro screen
        intro.undraw()
        jogar.undraw()
        sair.undraw()
        
    def setup_game_objects(self):
        """Initialize all game objects"""
        # Create field first (includes background)
        self.field = Field(x, y, self.window)
        
        # Create players
        self.player1 = Player(300, 503, True, self.window)
        self.player2 = Player(900, 503, False, self.window)
        
        # Create ball
        self.ball = Ball(x / 2, 100, self.window)
        
    def setup_score_display(self):
        """Initialize score display"""
        self.score_left = Text(Point(x / 2 - 20, 40), "0")
        self.score_left.setStyle("bold")
        self.score_left.setTextColor("white")
        self.score_left.setSize(25)
        self.score_left.draw(self.window)
        
        self.score_right = Text(Point(x / 2 + 20, 40), "0")
        self.score_right.setStyle("bold")
        self.score_right.setTextColor("white")
        self.score_right.setSize(25)
        self.score_right.draw(self.window)
        
    def handle_controls(self):
        """Process input from the active controller"""
        player_states = self.controller.process_input()
        
        # Handle Player 1
        if player_states[1]["movement"] == "left":
            self.player1.move(-vel, 0)
        elif player_states[1]["movement"] == "right":
            self.player1.move(vel, 0)
            
        if player_states[1]["jump"] == "jumping":
            self.player1.start_jump()
        if player_states[1]["kick"] == "kicking":
            self.player1.start_kick()
            
        # Handle Player 2
        if player_states[2]["movement"] == "left":
            self.player2.move(-vel, 0)
        elif player_states[2]["movement"] == "right":
            self.player2.move(vel, 0)
            
        if player_states[2]["jump"] == "jumping":
            self.player2.start_jump()
        if player_states[2]["kick"] == "kicking":
            self.player2.start_kick()
            
    def update_physics(self):
        """Update physics and collisions"""
        # Update player animations
        self.player1.update_jump()
        self.player1.update_kick()
        self.player2.update_jump()
        self.player2.update_kick()
        
        # Handle collisions first
        self.handle_collisions()
        
        # Check field boundaries and goal post collisions
        new_velx, new_vely = self.field.check_field_collision(
            self.ball.x, self.ball.y, raio, 
            self.ball.velx, self.ball.vely
        )
        self.ball.velx = new_velx
        self.ball.vely = new_vely
        
        # Then apply physics
        self.ball.apply_physics(atrito, chao)
        
        # Finally check for goals, but only if not already in goal state
        if not self.is_goal:
            is_goal, side = self.field.check_goal(self.ball.x, self.ball.y, raio)
            if is_goal:
                if side == "left":
                    self.score["left"] += 1
                else:
                    self.score["right"] += 1
                self.is_goal = True
        
    def handle_collisions(self):
        """Handle all collision checks and responses based on original game physics"""
        # Get current positions
        ball_x = self.ball.x
        ball_y = self.ball.y
        
        # Player 1 positions
        head1_x = self.player1.head.getCenter().getX()
        head1_y = self.player1.head.getCenter().getY()
        foot1_x = self.player1.foot.getCenter().getX()
        foot1_y = self.player1.foot.getCenter().getY()
        
        # Player 2 positions
        head2_x = self.player2.head.getCenter().getX()
        head2_y = self.player2.head.getCenter().getY()
        foot2_x = self.player2.foot.getCenter().getX()
        foot2_y = self.player2.foot.getCenter().getY()
        
        # Calculate collision distances
        head1_dist = math.hypot(head1_x - ball_x, head1_y - ball_y)
        foot1_dist = math.hypot(foot1_x - ball_x, foot1_y - ball_y)
        head2_dist = math.hypot(head2_x - ball_x, head2_y - ball_y)
        foot2_dist = math.hypot(foot2_x - ball_x, foot2_y - ball_y)
        
        COLLISION_DIST = 45  # Collision detection distance
        
        # Collision radius (reduced from 80)
        COLLISION_RADIUS = 40  # Slightly tighter collision detection
        RESTITUTION = 0.7  # Reduced bounciness for better control
        
        # Calculate distances
        head1_dist = math.hypot((head1_x - ball_x), (head1_y - ball_y))
        foot1_dist = math.hypot((foot1_x - ball_x), (foot1_y - ball_y))
        head2_dist = math.hypot((head2_x - ball_x), (head2_y - ball_y))
        foot2_dist = math.hypot((foot2_x - ball_x), (foot2_y - ball_y))
        
        # Player 1 collisions
        if head1_dist <= COLLISION_RADIUS or foot1_dist <= COLLISION_RADIUS:
            # Use closest point for collision
            if head1_dist <= foot1_dist:
                contact_x, contact_y = head1_x, head1_y
                is_foot = False
            else:
                contact_x, contact_y = foot1_x, foot1_y
                is_foot = True
                
            # Calculate collision normal
            dx = ball_x - contact_x
            dy = ball_y - contact_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                nx = dx/dist
                ny = dy/dist
                
                # Calculate collision response
                base_force = 5  # Base force for collisions
                
                if is_foot:
                    if self.player1.kicking:
                        # Patada más suave con más altura
                        kick_force = base_force * 1.8  # Reducido de 2.5 a 1.8
                        self.ball.velx = int(kick_force * 1.2 * nx)  # Reducido de 1.8 a 1.2
                        self.ball.vely = int(kick_force * -0.7)  # Aumentado de -0.4 a -0.7 para más altura
                    else:
                        # Normal foot touch
                        self.ball.velx = int(base_force * nx)
                        self.ball.vely = int(base_force * ny * -0.8)
                else:
                    # Head collision - simple parabolic motion for Player 1
                    self.ball.velx = 5  # Reducido de 7 a 5 para menos potencia
                    self.ball.vely = -8  # Ajustado de -9 a -8
                
                # Move ball out of collision
                separation_distance = COLLISION_RADIUS + 1
                ball_move_x = (contact_x + separation_distance * nx) - ball_x
                ball_move_y = (contact_y + separation_distance * ny) - ball_y
                self.ball.move(ball_move_x, ball_move_y)

                
                # Move ball out of collision
                
                separation_distance = COLLISION_RADIUS + 1
                ball_move_x = (contact_x + separation_distance * nx) - ball_x
                ball_move_y = (contact_y + separation_distance * ny) - ball_y
                self.ball.move(ball_move_x, ball_move_y)
                
        # Player 2 collisions
        if head2_dist <= COLLISION_RADIUS or foot2_dist <= COLLISION_RADIUS:
            # Use closest point for collision
            if head2_dist <= foot2_dist:
                contact_x, contact_y = head2_x, head2_y
                is_foot = False
            else:
                contact_x, contact_y = foot2_x, foot2_y
                is_foot = True
                
            # Calculate collision normal
            dx = ball_x - contact_x
            dy = ball_y - contact_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                nx = dx/dist
                ny = dy/dist
                
                # Calculate collision response
                base_force = 5  # Base force for collisions
                
                if is_foot:
                    if self.player2.kicking:
                        # Patada más suave con más altura
                        kick_force = base_force * 1.8  # Reducido de 2.5 a 1.8
                        self.ball.velx = int(kick_force * 1.2 * nx)  # Reducido de 1.8 a 1.2
                        self.ball.vely = int(kick_force * -0.7)  # Aumentado de -0.4 a -0.7 para más altura
                    else:
                        # Normal foot touch
                        self.ball.velx = int(base_force * nx)
                        self.ball.vely = int(base_force * ny * -0.8)
                else:
                    # Head collision - simple parabolic motion for Player 2
                    self.ball.velx = -5  # Reducido de -7 a -5 para menos potencia
                    self.ball.vely = -8  # Ajustado de -9 a -8
                
                # Move ball out of collision
                
                separation_distance = COLLISION_RADIUS + 1
                ball_move_x = (contact_x + separation_distance * nx) - ball_x
                ball_move_y = (contact_y + separation_distance * ny) - ball_y
                self.ball.move(ball_move_x, ball_move_y)
        
    def reset_after_goal(self):
        """Reset game state after a goal"""
        self.is_goal = False
        # Reset ball and player positions
        self.ball.reset(x / 2, 100)
        self.player1.set_position(300, 503)
        self.player2.set_position(900, 503)
        
        # Reset controller states to prevent stuck states
        if self.use_vision:
            self.vision_controller.reset_states()
            
        # Reset player states
        self.player1.jumping = False
        self.player1.kicking = False
        self.player2.jumping = False
        self.player2.kicking = False
        
        time.sleep(1)
        
    def update_display(self):
        """Update the game display"""
        self.score_left.setText(str(self.score["left"]))
        self.score_right.setText(str(self.score["right"]))
        self.window.update()
        
    def run(self):
        """Main game loop"""
        self.window.ligar_Buffer()
        
        while True:
            # Process player input
            self.handle_controls()
            
            # Update game state
            self.update_physics()
            
            # Update display
            self.update_display()
            
            # Handle goal scored
            if self.is_goal:
                self.reset_after_goal()
            
            # Add small delay for stable frame rate
            time.sleep(0.016)  # Aproximadamente 60 FPS
            
    def cleanup(self):
        """Clean up resources before exit"""
        if self.use_vision:
            self.vision_controller.cleanup()
        self.window.close()