import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    print("Dropping and recreating all tables...")
    db.drop_all()
    db.create_all()
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database() 