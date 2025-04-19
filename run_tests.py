#!/usr/bin/env python
import os
import shutil

def backup_file(filename):
    """Create a backup of the file"""
    backup_name = f"{filename}.bak"
    if os.path.exists(filename):
        shutil.copy(filename, backup_name)
        print(f"Created backup of {filename} as {backup_name}")
    
def update_file(filename):
    """Update app.py with fixed indentation"""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Fix indentation in the first try-except block in add_sample_courses
    if len(lines) >= 715 and "try:" in lines[709]:
        lines[710] = lines[710].replace("db.session.commit()", "            db.session.commit()")
        lines[711] = lines[711].replace('print("Admin user', '            print("Admin user')
        lines[713] = lines[713].replace("db.session.rollback()", "            db.session.rollback()")
        lines[714] = lines[714].replace('print(f"Error', '            print(f"Error')
        lines[715] = lines[715].replace("return", "            return")
    
    # Fix indentation in the second try-except block in add_sample_courses
    if len(lines) >= 760 and "try:" in lines[754]:
        lines[755] = lines[755].replace("db.session.commit()", "        db.session.commit()")
        lines[756] = lines[756].replace('print(f"Committed', '        print(f"Committed')
        lines[758] = lines[758].replace("db.session.rollback()", "        db.session.rollback()")
        lines[759] = lines[759].replace('print(f"Error', '        print(f"Error')
        lines[760] = lines[760].replace("return", "        return")
    
    # Save the changes
    with open(f"{filename}.fixed", 'w') as f:
        f.writelines(lines)
    
    print(f"Fixed indentation issues in {filename} and saved to {filename}.fixed")
    
    # Test if syntax is correct
    import ast
    try:
        with open(f"{filename}.fixed", 'r') as f:
            ast.parse(f.read())
        print("Syntax check PASSED!")
        
        # Replace the original file
        shutil.copy(f"{filename}.fixed", filename)
        print(f"Updated {filename} with fixed indentation")
        return True
    except SyntaxError as e:
        print(f"Syntax check FAILED: {e}")
        return False

if __name__ == "__main__":
    filename = "app.py"
    backup_file(filename)
    success = update_file(filename)
    print("Done" if success else "Failed to fix indentation issues") 