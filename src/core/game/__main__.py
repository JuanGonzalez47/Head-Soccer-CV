from .game import Game

def main():
    """Entry point for the game"""
    game = Game()
    try:
        game.run()
    finally:
        game.cleanup()

if __name__ == "__main__":
    main()
