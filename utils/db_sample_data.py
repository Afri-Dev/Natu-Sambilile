import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db, User, Course, Lesson, Quiz, QuizQuestion, QuizOption

def add_sample_data():
    """Add sample data to the database for testing and development"""
    print("Adding sample data...")
    
    # Create an admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        is_admin=True
    )
    admin.set_password("admin123")
    
    # Create a regular user
    user = User(
        username="student",
        email="student@example.com",
        is_admin=False
    )
    user.set_password("student123")
    
    # Add users to database
    db.session.add(admin)
    db.session.add(user)
    db.session.commit()
    
    # Create sample courses
    courses = [
        {
            'title': 'Python Programming',
            'description': 'Learn Python programming from basics to advanced concepts',
            'semantic_tags': 'Python,Programming,Beginner',
            'duration_weeks': 8
        },
        {
            'title': 'Web Development',
            'description': 'Master modern web development with HTML, CSS and JavaScript',
            'semantic_tags': 'Web,HTML,CSS,JavaScript',
            'duration_weeks': 10
        },
        {
            'title': 'Data Science Fundamentals',
            'description': 'Introduction to data analysis and visualization',
            'semantic_tags': 'Data,Analysis,Python,Statistics',
            'duration_weeks': 12
        }
    ]
    
    created_courses = []
    for course_data in courses:
        course = Course(
            title=course_data['title'],
            description=course_data['description'],
            semantic_tags=course_data['semantic_tags'],
            duration_weeks=course_data['duration_weeks'],
            user_id=admin.id
        )
        db.session.add(course)
        created_courses.append(course)
    
    db.session.commit()
    print(f"Added {len(created_courses)} courses")
    
    # Create sample lessons for each course
    lesson_count = 0
    for course in created_courses:
        for i in range(1, 6):  # 5 lessons per course
            lesson = Lesson(
                title=f"Lesson {i}: {course.title}",
                content=f"Content for lesson {i} of {course.title}",
                lesson_number=i,
                course_id=course.id,
                video_url=f"https://example.com/videos/{course.id}/lesson{i}.mp4",
                resources=f"Additional resources for {course.title} lesson {i}",
                duration_minutes=45
            )
            db.session.add(lesson)
            lesson_count += 1
    
    db.session.commit()
    print(f"Added {lesson_count} lessons")
    
    # Create quizzes for the first course's lessons
    quiz_count = 0
    for lesson in Lesson.query.filter_by(course_id=created_courses[0].id).all():
        quiz = Quiz(
            title=f"Quiz for {lesson.title}",
            lesson_id=lesson.id
        )
        db.session.add(quiz)
        db.session.flush()  # Get the quiz ID for questions
        
        # Add questions to each quiz
        for q in range(1, 4):  # 3 questions per quiz
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=f"Question {q} for {lesson.title}?"
            )
            db.session.add(question)
            db.session.flush()  # Get the question ID for options
            
            # Add options to each question
            for o in range(1, 5):  # 4 options per question
                option = QuizOption(
                    quiz_question_id=question.id,
                    option_text=f"Option {o} for question {q}",
                    is_correct=(o == 1)  # First option is correct
                )
                db.session.add(option)
        
        quiz_count += 1
    
    db.session.commit()
    print(f"Added {quiz_count} quizzes with questions and options")
    
    print("\nSample data added successfully!")
    print("\nSample accounts:")
    print("- Admin: admin@example.com / admin123")
    print("- Student: student@example.com / student123")

if __name__ == "__main__":
    add_sample_data() 