#!/usr/bin/env python

# Read the file
with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix try-except blocks at specific problematic locations

# Add sample courses function - first try block
if 'try:' in lines[709] and 'db.session.commit()' in lines[710]:
    lines[710] = '            db.session.commit()\n'
    lines[711] = '            print("Admin user created/verified.")\n'
    lines[712] = '        except Exception as e:\n'
    lines[713] = '            db.session.rollback()\n'
    lines[714] = '            print(f"Error adding admin user: {e}")\n'
    lines[715] = '            return # Stop if admin can\'t be added\n'

# Add sample courses function - second try block
if 'try:' in lines[754]:
    lines[755] = '        db.session.commit()\n'
    lines[756] = '        print(f"Committed course additions/checks.")\n'
    lines[757] = '    except Exception as e:\n'
    lines[758] = '        db.session.rollback()\n'
    lines[759] = '        print(f"Error committing courses: {e}")\n'
    lines[760] = '        return\n'

# Save the updated file
with open('app_fixed.py', 'w') as f:
    f.writelines(lines)

print("Updated try-except blocks in app_fixed.py") 