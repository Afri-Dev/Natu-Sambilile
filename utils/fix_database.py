import os
import sys
import sqlite3
from sqlite3 import Error

# Add parent directory to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    return column in column_names

def fix_database(db_path):
    """Fix the database schema by adding missing columns"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist.")
        return
    
    print(f"\nChecking database at {db_path}...")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the lesson table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lesson'")
        if not cursor.fetchone():
            print(f"Table 'lesson' does not exist in {db_path}.")
            return
        
        # Check and add video_url column
        if not check_column_exists(cursor, 'lesson', 'video_url'):
            print(f"Adding 'video_url' column to lesson table in {db_path}...")
            cursor.execute("ALTER TABLE lesson ADD COLUMN video_url TEXT")
            print("Added 'video_url' column successfully.")
        else:
            print("Column 'video_url' already exists.")
        
        # Check and add resources column
        if not check_column_exists(cursor, 'lesson', 'resources'):
            print(f"Adding 'resources' column to lesson table in {db_path}...")
            cursor.execute("ALTER TABLE lesson ADD COLUMN resources TEXT")
            print("Added 'resources' column successfully.")
        else:
            print("Column 'resources' already exists.")
        
        # Check and add duration_minutes column
        if not check_column_exists(cursor, 'lesson', 'duration_minutes'):
            print(f"Adding 'duration_minutes' column to lesson table in {db_path}...")
            cursor.execute("ALTER TABLE lesson ADD COLUMN duration_minutes INTEGER DEFAULT 60")
            print("Added 'duration_minutes' column successfully.")
        else:
            print("Column 'duration_minutes' already exists.")
        
        conn.commit()
        print(f"Database check complete for {db_path}")
        
    except Error as e:
        print(f"Database error with {db_path}: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """Main function to fix all database files"""
    print("Database Schema Repair Tool")
    print("==========================")
    
    # Check both potential database locations
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_paths = [
        os.path.join(parent_dir, 'instance', 'elearning.db'),
        os.path.join(parent_dir, 'elearning.db')
    ]
    
    for db_path in db_paths:
        fix_database(db_path)
    
    print("\nRepair process completed. Please restart your Flask application.")

if __name__ == "__main__":
    main() 