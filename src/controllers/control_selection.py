from src.graphics.graphics import Image, Point, Rectangle, Text
from PIL import Image as PILImage
import os
import time

class ControlSelector:
    def __init__(self, window):
        """Initialize the control selection screen
        
        Args:
            window: The game window to draw on
        """
        self.window = window
        
    def create_button(self, center_x, center_y, width, height, text, color="white"):
        """Create a button with text
        
        Args:
            center_x: X coordinate of button center
            center_y: Y coordinate of button center
            width: Button width
            height: Button height
            text: Button text
            color: Button color (default: white)
        """
        # Create button rectangle
        button = Rectangle(
            Point(center_x - width/2, center_y - height/2),
            Point(center_x + width/2, center_y + height/2)
        )
        button.setFill(color)
        button.setOutline("white")
        button.setWidth(2)  # Make the border thicker
        
        # Create button text
        text_obj = Text(Point(center_x, center_y), text)
        text_obj.setTextColor("white")
        text_obj.setSize(16)
        text_obj.setStyle("bold")
        
        return button, text_obj
        
    def show_selection_screen(self, x, y):
        """Show the control selection screen and return the user's choice
        
        Args:
            x: Window width
            y: Window height
            
        Returns:
            str: 'vision' for gesture controls, 'keyboard' for keyboard controls
        """
        print("Mostrando pantalla de selección...")  # Debug print
        
        # Load the GIF background image directly
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        bg_image_path = os.path.join(src_dir, "src", "assets", "images", "istockphoto-1204755567-612x612.gif")
        
        try:
            print(f"Loading background image from: {bg_image_path}")
            if os.path.exists(bg_image_path):
                # Creamos un rectángulo blanco del tamaño de la ventana
                bg_rect = Rectangle(Point(0, 0), Point(x, y))
                bg_rect.setFill("white")
                bg_rect.setWidth(0)
                bg_rect.draw(self.window)

                # Abrimos la imagen GIF con PIL y la redimensionamos
                pil_img = PILImage.open(bg_image_path)
                # Redimensionar manteniendo proporción para cubrir la ventana
                orig_w, orig_h = pil_img.size
                scale_x = x / orig_w
                scale_y = y / orig_h
                scale = max(scale_x, scale_y)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                pil_img = pil_img.resize((new_w, new_h), PILImage.LANCZOS)

                # Guardar imagen temporalmente
                temp_path = os.path.join(os.path.dirname(bg_image_path), "_temp_bg.gif")
                pil_img.save(temp_path, format="GIF")

                # Cargar la imagen escalada en el objeto Image
                background = Image(Point(x/2, y/2), temp_path)
                background.draw(self.window)
                print(f"Successfully set background image with scale factor: {scale}")
                bg_image = background
            
        except Exception as e:
            print(f"Error setting background image: {e}")
            import traceback
            traceback.print_exc()  # Print detailed error information
            bg_image = None
            self.window.setBackground("#1a472a")  # Fallback color
        
        
        # Create title text
        title = Text(Point(x/2, 150), "How do You Want to Play?")
        title.setTextColor("white")
        title.setSize(32)
        title.setStyle("bold")
        title.draw(self.window)
        
        # Create buttons with dark green background and larger size
        vision_button, vision_text = self.create_button(450, 300, 250, 80, "Vision Control", "darkgreen")
        keyboard_button, keyboard_text = self.create_button(750, 300, 250, 80, "Keyboard Control", "darkgreen")

        # Draw buttons
        vision_button.draw(self.window)
        vision_text.draw(self.window)
        keyboard_button.draw(self.window)
        keyboard_text.draw(self.window)
        
        # Wait for player selection
        while True:
            click = self.window.checkMouse()
            key = self.window.checkKey()
            
            if click:
                click_x = click.getX()
                click_y = click.getY()
                
                # Vision control button area (adjusted for larger buttons)
                if (260 <= click_y <= 340) and (175 <= click_x <= 425):
                    selection = "vision"
                    break
                    
                # Keyboard control button area (adjusted for larger buttons)
                elif (260 <= click_y <= 340) and (575 <= click_x <= 825):
                    selection = "keyboard"
                    break
            
            # Allow keyboard selection too
            elif key:
                if key.lower() == "v":
                    selection = "vision"
                    break
                elif key.lower() == "k":
                    selection = "keyboard"
                    break
            
            time.sleep(0.016)  # Add a small delay to prevent high CPU usage
        
        # Add a small delay before cleaning up
        time.sleep(0.2)
        
        # Clean up all elements
        for item in [title, vision_button, vision_text, 
                    keyboard_button, keyboard_text]:
            try:
                item.undraw()
            except:
                pass
                
        # Clean up background elements
        if 'bg_rect' in locals():
            bg_rect.undraw()
                
        # Clean up background image last
        if bg_image is not None:
            try:
                bg_image.undraw()
            except:
                pass
        
        # Add a small delay after cleaning up
        time.sleep(0.2)
        
        return selection