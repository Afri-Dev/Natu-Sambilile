#!/usr/bin/env python

def fix_indentation(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Fix indentation in try/except blocks
    lines = content.splitlines()
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check for try: blocks
        if line.strip() == 'try:':
            i += 1
            if i < len(lines):
                next_line = lines[i]
                # If next line is not indented properly
                if not next_line.startswith('    ') and next_line.strip() and not next_line.strip().startswith(('except', 'finally')):
                    fixed_lines.append('    ' + next_line.lstrip())
                else:
                    fixed_lines.append(next_line)
        # Fix specific indentation errors
        elif i == 710 and 'db.session.commit()' in line:
            fixed_lines[-1] = '            db.session.commit()'
        elif i == 754 and 'db.session.commit()' in line:
            fixed_lines[-1] = '        db.session.commit()'
        elif i == 889 and 'db.session.commit()' in line:
            fixed_lines[-1] = '        db.session.commit()'
        elif i == 978 and 'db.session.commit()' in line:
            fixed_lines[-1] = '        db.session.commit()'
        elif i == 1044 and 'db.session.commit()' in line:
            fixed_lines[-1] = '        db.session.commit()'
        elif i == 1062 and 'db.session.commit()' in line:
            fixed_lines[-1] = '            db.session.commit()'
        elif i == 1096 and 'db.session.commit()' in line:
            fixed_lines[-1] = '                db.session.commit()'
        elif i == 1112 and 'db.session.commit()' in line:
            fixed_lines[-1] = '        db.session.commit()'
        elif i == 1193 and 'print("SEED_DATA is True' in line:
            fixed_lines[-1] = '            print("SEED_DATA is True. Attempting to add sample data...")'
        elif i == 1194 and 'add_sample_courses()' in line:
            fixed_lines[-1] = '            add_sample_courses()'
        elif i == 1195 and 'else:' in line:
            fixed_lines[-1] = '        else:'
        elif i == 1196 and 'print("SEED_DATA is False' in line:
            fixed_lines[-1] = '            print("SEED_DATA is False. Skipping add_sample_courses.")'
        
        i += 1
    
    # Write the fixed content
    with open(output_file, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed indentation issues in {input_file} and saved to {output_file}")

if __name__ == "__main__":
    fix_indentation('app.py', 'app_fixed.py') 