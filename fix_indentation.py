#!/usr/bin/env python3

def fix_indentation():
    with open('app.py', 'r') as f:
        lines = f.readlines()
    
    # Fix the first indentation issue (line 825)
    if "try:" in lines[824]:
        lines[825] = "        db.session.commit()\n"
    
    # Fix the second indentation issue (line 982)
    if "db.session.add(lesson)" in lines[981]:
        lines[982] = "        db.session.commit()\n"
    
    # Fix the third indentation issue (line 1289 - if-else block)
    for i in range(1280, 1290):
        if "if SEED_DATA:" in lines[i]:
            # Fix indentation of add_sample_courses() and else statement
            for j in range(i+2, i+5):
                if "add_sample_courses()" in lines[j]:
                    lines[j] = "            add_sample_courses()\n"
                if "else:" in lines[j]:
                    lines[j] = "        else:\n"
    
    with open('app.py', 'w') as f:
        f.writelines(lines)
    
    print("Indentation issues fixed!")

if __name__ == "__main__":
    fix_indentation() 