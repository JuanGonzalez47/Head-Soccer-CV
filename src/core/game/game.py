import os
import sys
import time
import math
from src.graphics.graphics import GraphWin, Point, Text, Image, Rectangle
from src.core.config import (
    x, y, raio, raio_cabeca, chao, vel, atrito,
    larg_t, alt_t, contador_gol1, contador_gol2
)
from src.core.game.ball import Ball
from src.core.game.field import Field
from src.core.game.player import Player
from src.controllers.vision import VisionController
from src.controllers.keyboard import KeyboardController
from src.controllers.control_selection import ControlSelector

class Game:
    def __init__(self):
        """Initialize the game window and all components"""
        print("[INFO] Initializing game...")
        # Create main window
        self.window = GraphWin("Head Soccer", x, y, False)
        self.window.setBackground("black")
        # Initialize game state
        self.score = {"left": 0, "right": 0}
        self.is_goal = False
        # Initialize controllers first
        self.setup_controllers()
        # Then show intro screen
        self.show_intro()
        # Initialize game objects
        self.setup_game_objects()
        # Initialize score display
        self.setup_score_display()
        # Enable key buffer for better keyboard response
        self.window.ligar_Buffer()
        

    def set_controller(self, control_type):
        """Set the active controller based on control_type ('vision' or 'keyboard')."""
        print(f"[INFO] Setting controller: {control_type}")
        try:
            if control_type == "vision":
                # Clean up previous vision controller if exists
                if hasattr(self, 'vision_controller') and self.vision_controller is not None:
                    try:
                        self.vision_controller.cleanup()
                    except Exception:
                        pass
                self.vision_controller = VisionController()
                self.controller = self.vision_controller
                self.use_vision = True
                print("[INFO] Vision controller is now active.")
            else:
                # Clean up previous vision controller if switching to keyboard
                if hasattr(self, 'vision_controller') and self.vision_controller is not None:
                    try:
                        self.vision_controller.cleanup()
                    except Exception:
                        pass
                self.controller = KeyboardController(self.window)
                self.use_vision = False
                print("[INFO] Keyboard controller is now active.")
        except Exception as e:
            print(f"[ERROR] Error initializing controller: {e}")
            print("[ERROR] Falling back to keyboard controls")
            self.controller = KeyboardController(self.window)
            self.use_vision = False
        time.sleep(0.5)

    def setup_controllers(self):
        """Show control selection screen and set controller."""
        print("[INFO] Setting up controllers...")
        selector = ControlSelector(self.window)
        control_type = selector.show_selection_screen(x, y)
        print(f"[INFO] Control type selected: {control_type}")
        self.set_controller(control_type)
            
    def show_intro(self):
        """Show and handle the intro screen with custom buttons"""
        # Background image (optional, keep as before)
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        image_dir = os.path.join(src_dir, "assets", "images")
        intro_bg = Image(Point(x / 2, y / 2), os.path.join(image_dir, "intro2.gif"))
        intro_bg.draw(self.window)

        # Button positions and sizes
        btn_w, btn_h = 220, 70
        play_btn_cx, play_btn_cy = 175, 500
        exit_btn_cx, exit_btn_cy = 425, 500
        select_ctrl_btn_cx, select_ctrl_btn_cy = 675, 500

        # Create Play button (green)
        play_btn_rect = Rectangle(
            Point(play_btn_cx - btn_w/2, play_btn_cy - btn_h/2),
            Point(play_btn_cx + btn_w/2, play_btn_cy + btn_h/2)
        )
        play_btn_rect.setFill("#228b22")
        play_btn_rect.setOutline("white")
        play_btn_rect.setWidth(2)
        play_btn_rect.draw(self.window)
        play_btn_text = Text(Point(play_btn_cx, play_btn_cy), "Play")
        play_btn_text.setTextColor("white")
        play_btn_text.setSize(20)
        play_btn_text.setStyle("bold")
        play_btn_text.draw(self.window)

        # Create Exit button (dark green)
        exit_btn_rect = Rectangle(
            Point(exit_btn_cx - btn_w/2, exit_btn_cy - btn_h/2),
            Point(exit_btn_cx + btn_w/2, exit_btn_cy + btn_h/2)
        )
        exit_btn_rect.setFill("darkgreen")
        exit_btn_rect.setOutline("white")
        exit_btn_rect.setWidth(2)
        exit_btn_rect.draw(self.window)
        exit_btn_text = Text(Point(exit_btn_cx, exit_btn_cy), "Exit")
        exit_btn_text.setTextColor("white")
        exit_btn_text.setSize(20)
        exit_btn_text.setStyle("bold")
        exit_btn_text.draw(self.window)

        # Create Select Controls button (green)
        select_ctrl_btn_rect = Rectangle(
            Point(select_ctrl_btn_cx - btn_w/2, select_ctrl_btn_cy - btn_h/2),
            Point(select_ctrl_btn_cx + btn_w/2, select_ctrl_btn_cy + btn_h/2)
        )
        select_ctrl_btn_rect.setFill("#228b22")
        select_ctrl_btn_rect.setOutline("white")
        select_ctrl_btn_rect.setWidth(2)
        select_ctrl_btn_rect.draw(self.window)
        select_ctrl_btn_text = Text(Point(select_ctrl_btn_cx, select_ctrl_btn_cy), "Select Controls")
        select_ctrl_btn_text.setTextColor("white")
        select_ctrl_btn_text.setSize(20)
        select_ctrl_btn_text.setStyle("bold")
        select_ctrl_btn_text.draw(self.window)

        # Wait for player input
        while True:
            enter = self.window.checkKey()
            check = self.window.checkMouse()
            if check is not None:
                check_x = check.getX()
                check_y = check.getY()
                # Play button
                if (play_btn_cx - btn_w/2 <= check_x <= play_btn_cx + btn_w/2) and (play_btn_cy - btn_h/2 <= check_y <= play_btn_cy + btn_h/2):
                    time.sleep(0.06)
                    break
                # Exit button
                elif (exit_btn_cx - btn_w/2 <= check_x <= exit_btn_cx + btn_w/2) and (exit_btn_cy - btn_h/2 <= check_y <= exit_btn_cy + btn_h/2):
                    time.sleep(0.2)
                    if self.use_vision:
                        self.vision_controller.cleanup()
                    self.window.close()
                    sys.exit()
                # Select Controls button
                elif (select_ctrl_btn_cx - btn_w/2 <= check_x <= select_ctrl_btn_cx + btn_w/2) and (select_ctrl_btn_cy - btn_h/2 <= check_y <= select_ctrl_btn_cy + btn_h/2):
                    print("[INFO] Select Controls from intro screen")
                    selector = ControlSelector(self.window)
                    control_type = selector.show_selection_screen(x, y)
                    print(f"[INFO] New control selected: {control_type}")
                    self.set_controller(control_type)
            else:
                if enter == "Return":
                    time.sleep(0.06)
                    break
            time.sleep(0.07)

        # Clear intro screen
        intro_bg.undraw()
        play_btn_rect.undraw()
        play_btn_text.undraw()
        exit_btn_rect.undraw()
        exit_btn_text.undraw()
        select_ctrl_btn_rect.undraw()
        select_ctrl_btn_text.undraw()
        
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
        try:
            # Only print controller type at each frame
            # print(f"[DEBUG] handle_controls: using controller {type(self.controller).__name__}")
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
        except Exception as e:
            print(f"[ERROR] Error handling controls: {e}")
            
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
        """Main game loop con botones de navegación"""
        # Make sure key buffer is enabled
        if hasattr(self.window, 'ligar_Buffer'):
            self.window.ligar_Buffer()

        # Add navigation buttons in the top-right and top-left corners
        btn_width, btn_height = 150, 40
        margin = 10
        # Exit button (top-right)
        exit_btn_rect = Rectangle(
            Point(x - btn_width - margin, margin),
            Point(x - margin, margin + btn_height)
        )
        exit_btn_rect.setFill("#b22222")  # Red
        exit_btn_rect.setOutline("white")
        exit_btn_rect.setWidth(2)
        exit_btn_rect.draw(self.window)
        exit_btn_text = Text(
            Point(x - btn_width/2 - margin, margin + btn_height/2), "Exit"
        )
        exit_btn_text.setTextColor("white")
        exit_btn_text.setSize(14)
        exit_btn_text.setStyle("bold")
        exit_btn_text.draw(self.window)

        # Select Controls button (top-right, left of Exit)
        select_ctrl_btn_rect = Rectangle(
            Point(x - 2*btn_width - 2*margin, margin),
            Point(x - btn_width - 2*margin, margin + btn_height)
        )
        select_ctrl_btn_rect.setFill("#228b22")  # Green
        select_ctrl_btn_rect.setOutline("white")
        select_ctrl_btn_rect.setWidth(2)
        select_ctrl_btn_rect.draw(self.window)
        select_ctrl_btn_text = Text(
            Point((x - 1.5*btn_width - 1.5*margin) - 7, margin + btn_height/2), "Select Controls"
        )
        select_ctrl_btn_text.setTextColor("white")
        select_ctrl_btn_text.setSize(12)
        select_ctrl_btn_text.setStyle("bold")
        select_ctrl_btn_text.draw(self.window)

        # Restart Match button (top-left)
        restart_btn_rect = Rectangle(
            Point(margin, margin),
            Point(margin + btn_width, margin + btn_height)
        )
        restart_btn_rect.setFill("#1e90ff")  # Blue
        restart_btn_rect.setOutline("white")
        restart_btn_rect.setWidth(2)
        restart_btn_rect.draw(self.window)
        restart_btn_text = Text(
            Point(margin + btn_width/2, margin + btn_height/2), "Restart Match"
        )
        restart_btn_text.setTextColor("white")
        restart_btn_text.setSize(12)
        restart_btn_text.setStyle("bold")
        restart_btn_text.draw(self.window)

        while True:
            # Handle mouse input for navigation buttons
            click = self.window.checkMouse()
            if click:
                cx, cy = click.getX(), click.getY()
                # Restart Match button (top-left)
                if (margin <= cx <= margin + btn_width) and (margin <= cy <= margin + btn_height):
                    print("[INFO] Restarting match...")
                    self.score = {"left": 0, "right": 0}
                    self.is_goal = False
                    self.ball.reset(x / 2, 100)
                    self.player1.set_position(300, 503)
                    self.player2.set_position(900, 503)
                    self.player1.jumping = False
                    self.player1.kicking = False
                    self.player2.jumping = False
                    self.player2.kicking = False
                    self.update_display()
                    continue
                # Exit button (top-right)
                if (x - btn_width - margin <= cx <= x - margin) and (margin <= cy <= margin + btn_height):
                    # Show confirmation dialog
                    confirm_bg = Rectangle(Point(x/2 - 180, y/2 - 80), Point(x/2 + 180, y/2 + 80))
                    confirm_bg.setFill("#222")
                    confirm_bg.setOutline("white")
                    confirm_bg.setWidth(3)
                    confirm_bg.draw(self.window)
                    confirm_text = Text(Point(x/2, y/2 - 30), "Are you sure you want to quit?")
                    confirm_text.setTextColor("white")
                    confirm_text.setSize(18)
                    confirm_text.setStyle("bold")
                    confirm_text.draw(self.window)
                    # Resume button
                    resume_btn = Rectangle(Point(x/2 - 140, y/2 + 20), Point(x/2 - 10, y/2 + 60))
                    resume_btn.setFill("#228b22")
                    resume_btn.setOutline("white")
                    resume_btn.setWidth(2)
                    resume_btn.draw(self.window)
                    resume_text = Text(Point(x/2 - 75, y/2 + 40), "Resume")
                    resume_text.setTextColor("white")
                    resume_text.setSize(14)
                    resume_text.setStyle("bold")
                    resume_text.draw(self.window)
                    # Quit button
                    quit_btn = Rectangle(Point(x/2 + 10, y/2 + 20), Point(x/2 + 140, y/2 + 60))
                    quit_btn.setFill("#b22222")
                    quit_btn.setOutline("white")
                    quit_btn.setWidth(2)
                    quit_btn.draw(self.window)
                    quit_text = Text(Point(x/2 + 75, y/2 + 40), "Quit Game")
                    quit_text.setTextColor("white")
                    quit_text.setSize(14)
                    quit_text.setStyle("bold")
                    quit_text.draw(self.window)
                    # Wait for user choice
                    while True:
                        confirm_click = self.window.checkMouse()
                        if confirm_click:
                            cfx, cfy = confirm_click.getX(), confirm_click.getY()
                            # Resume
                            if (x/2 - 140 <= cfx <= x/2 - 10) and (y/2 + 20 <= cfy <= y/2 + 60):
                                # Undraw dialog
                                for item in [confirm_bg, confirm_text, resume_btn, resume_text, quit_btn, quit_text]:
                                    try:
                                        item.undraw()
                                    except:
                                        pass
                                break  # Return to match
                            # Quit
                            elif (x/2 + 10 <= cfx <= x/2 + 140) and (y/2 + 20 <= cfy <= y/2 + 60):
                                self.cleanup()
                                sys.exit()
                        time.sleep(0.05)
                    continue  # Skip rest of loop to avoid double input
                # Select Controls button (top-right)
                elif (x - 2*btn_width - 2*margin <= cx <= x - btn_width - 2*margin) and (margin <= cy <= margin + btn_height):
                    print("[INFO] Select Controls button pressed")
                    # Go to control selection screen
                    selector = ControlSelector(self.window)
                    control_type = selector.show_selection_screen(x, y)
                    print(f"[INFO] New control selected: {control_type}")
                    # Reassign controller
                    self.set_controller(control_type)

            # Normal game controls
            self.handle_controls()
            self.update_physics()
            self.update_display()

            if self.is_goal:
                self.reset_after_goal()
            time.sleep(0.016)
            if self.window.isClosed():
                break
            
    def cleanup(self):
        """Clean up resources before exit"""
        if self.use_vision:
            self.vision_controller.cleanup()
        self.window.close()