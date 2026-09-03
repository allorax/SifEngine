"""CLI command to initialize SQLite database tables."""
import sys
from app.database import init_database


def main():
    print("Initializing SQLite database tables...")
    try:
        init_database()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
