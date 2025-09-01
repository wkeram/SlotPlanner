from app.gui import run_application
from app.config.logging_config import AppLogger


def main():
    """Entry point for the SlotPlanner application."""
    # Initialize logging configuration
    AppLogger()
    return run_application()


if __name__ == "__main__":
    main()
