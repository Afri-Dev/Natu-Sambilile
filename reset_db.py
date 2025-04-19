import os
from app import db

def reset_database():
    """Reset the database by recreating all tables"""
    print("Resetting database...")

    # Remove existing database files
    for db_path in ["instance/elearning.db", "elearning.db"]:
        if os.path.exists(db_path):
            print(f"Removing existing database at {db_path}")
            os.remove(db_path)

    # Create all tables in the new database
    print("Creating new database tables...")
    db.create_all()
    print("Database reset successful!")

if __name__ == "__main__":
    reset_database()
