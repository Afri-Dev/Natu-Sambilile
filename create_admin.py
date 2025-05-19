import sys
from getpass import getpass
from werkzeug.security import generate_password_hash
import os
import sqlite3
from datetime import datetime

def connect_to_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect('elearning.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_admin_user():
    """Create a new admin user."""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        print("\n=== Create Admin User ===")
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        password = getpass("Enter admin password: ").strip()
        confirm_password = getpass("Confirm admin password: ").strip()
        
        if password != confirm_password:
            print("\n❌ Error: Passwords do not match!")
            return
        
        # Check if user already exists
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"\n❌ Error: User with email {email} already exists!")
            return
        
        # Create new admin user
        # Use named parameters instead of positional ones to avoid deprecation warning
        cursor.execute(
            "INSERT INTO user (username, email, password_hash, is_admin, created_at) VALUES (:username, :email, :password_hash, :is_admin, :created_at)",
            {
                "username": username, 
                "email": email, 
                "password_hash": generate_password_hash(password), 
                "is_admin": True, 
                "created_at": datetime.utcnow()
            }
        )
        conn.commit()
        print(f"\n✅ Admin user '{username}' created successfully!")
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
    finally:
        conn.close()

def list_admin_users():
    """List all admin users."""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, created_at FROM user WHERE is_admin = 1")
        admins = cursor.fetchall()
        
        if not admins:
            print("\nNo admin users found!")
            return
        
        print("\n=== Admin Users ===")
        for i, admin in enumerate(admins, 1):
            created_at = admin['created_at']
            print(f"{i}. ID: {admin['id']} | Username: {admin['username']} | Email: {admin['email']} | Created: {created_at}")
    except Exception as e:
        print(f"\n❌ Error listing admin users: {e}")
    finally:
        conn.close()

def delete_admin_user():
    """Delete an admin user."""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM user WHERE is_admin = 1")
        admins = cursor.fetchall()
        
        if not admins:
            print("\nNo admin users found!")
            return
        
        print("\n=== Delete Admin User ===")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin['username']} <{admin['email']}>")
        
        try:
            choice = int(input("\nEnter the number of the admin to delete (or 0 to cancel): "))
            if choice == 0:
                return
            
            if choice < 1 or choice > len(admins):
                print("\n❌ Invalid selection!")
                return
            
            admin = admins[choice-1]
            confirm = input(f"Are you sure you want to delete admin '{admin['username']}'? (y/n): ").lower()
            if confirm == 'y':
                cursor.execute("DELETE FROM user WHERE id = ?", (admin['id'],))
                conn.commit()
                print(f"\n✅ Admin user '{admin['username']}' deleted successfully!")
        except ValueError:
            print("\n❌ Invalid input! Please enter a number.")
    except Exception as e:
        print(f"\n❌ Error deleting admin user: {e}")
    finally:
        conn.close()

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("\nUsage: python create_admin.py <command>")
        print("\nCommands:")
        print("  create    - Create a new admin user")
        print("  list      - List all admin users")
        print("  delete    - Delete an admin user")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        create_admin_user()
    elif command == 'list':
        list_admin_users()
    elif command == 'delete':
        delete_admin_user()
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Use 'create', 'list', or 'delete' as the command.")

if __name__ == "__main__":
    main()