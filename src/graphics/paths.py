"""Path configuration for game assets."""
import os

# Get the absolute path to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Define asset paths
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "Imagens")

def get_asset_path(filename):
    """Get absolute path for an asset file."""
    return os.path.join(IMAGES_DIR, filename)