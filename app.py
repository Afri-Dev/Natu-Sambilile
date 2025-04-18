from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from datetime import datetime
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elearning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the ontology namespace
ELEARN = Namespace("http://example.org/elearning#")
g = Graph()
g.bind("elearn", ELEARN)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    semantic_tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    max_students = db.Column(db.Integer, default=50)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_weeks = db.Column(db.Integer, default=12)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    progress = db.Column(db.Float, default=0.0)  # 0 to 100
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)

class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prerequisites = db.Column(db.Text)
    course_sequence = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship('Course', backref='lessons', lazy=True)

class LessonCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    lesson = db.relationship('Lesson', backref='quiz', lazy=True)
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True)

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.relationship('QuizOption', backref='question', lazy=True)

class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context Processor to inject variables into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow} # Use utcnow for consistency

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('home'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    # Get featured courses (latest 3 courses)
    featured_courses = Course.query.order_by(Course.created_at.desc()).limit(3).all()
    
    # Get total statistics
    stats = {
        'total_courses': Course.query.count(),
        'total_students': User.query.count(),
        'total_enrollments': Enrollment.query.count()
    }
    
    # Get course categories (from semantic tags)
    categories = set()
    courses = Course.query.all()
    for course in courses:
        if course.semantic_tags:
            categories.update(tag.strip() for tag in course.semantic_tags.split(','))
    
    # Get latest courses (different from featured)
    latest_courses = Course.query.order_by(Course.created_at.desc()).offset(3).limit(4).all()
    
    return render_template('index.html', 
                         featured_courses=featured_courses,
                         latest_courses=latest_courses,
                         stats=stats,
                         categories=sorted(list(categories)))

@app.route('/courses')
@login_required
def courses():
    courses = Course.query.all()
    # Get enrollment status for each course
    user_enrollments = {e.course_id: e for e in current_user.enrollments}
    return render_template('courses.html', courses=courses, user_enrollments=user_enrollments)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, 
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({
            'status': 'error',
            'message': 'You are already enrolled in this course'
        }), 400
    
    # Check if course is full
    current_enrollments = Enrollment.query.filter_by(course_id=course_id).count()
    if current_enrollments >= course.max_students:
        return jsonify({
            'status': 'error',
            'message': 'Course is full'
        }), 400
    
    # Create enrollment
    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.session.add(enrollment)
    
    # Add to RDF graph
    enrollment_uri = ELEARN[f"enrollment_{enrollment.id}"]
    student_uri = ELEARN[f"user_{current_user.id}"]
    course_uri = ELEARN[f"course_{course.title.lower().replace(' ', '_')}"]
    
    g.add((enrollment_uri, RDF.type, ELEARN.Enrollment))
    g.add((enrollment_uri, ELEARN.hasStudent, student_uri))
    g.add((enrollment_uri, ELEARN.hasCourse, course_uri))
    g.add((enrollment_uri, ELEARN.enrollmentDate, Literal(enrollment.enrolled_at)))
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Successfully enrolled in {course.title}',
        'enrollment_id': enrollment.id
    })

@app.route('/unenroll/<int:course_id>', methods=['POST'])
@login_required
def unenroll(course_id):
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first_or_404()
    
    db.session.delete(enrollment)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Successfully unenrolled from the course'
    })

@app.route('/my-courses')
@login_required
def my_courses():
    # Eager load course and its lessons for each enrollment
    enrollments = Enrollment.query.options(
        joinedload(Enrollment.course).joinedload(Course.lessons)
    ).filter_by(user_id=current_user.id).all()
    
    # Also fetch completed lesson IDs for the current user to pass to template
    completed_lesson_ids = {comp.lesson_id for comp in LessonCompletion.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('my_courses.html', 
                         enrollments=enrollments,
                         completed_lesson_ids=completed_lesson_ids)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    # Eager load the course relationship when fetching the lesson
    lesson = Lesson.query.options(joinedload(Lesson.course)).get_or_404(lesson_id)
    course = lesson.course # Already loaded, no extra query
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first_or_404() # Ensures user is enrolled to view lesson
    
    # Get previous and next lessons
    prev_lesson = Lesson.query.filter(
        Lesson.course_id == course.id,
        Lesson.lesson_number < lesson.lesson_number
    ).order_by(Lesson.lesson_number.desc()).first()
    
    next_lesson = Lesson.query.filter(
        Lesson.course_id == course.id,
        Lesson.lesson_number > lesson.lesson_number
    ).order_by(Lesson.lesson_number.asc()).first()
    
    # Check if lesson is completed
    lesson_completed = LessonCompletion.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson.id
    ).first() is not None
    
    return render_template('lesson.html',
                         lesson=lesson,
                         course=course,
                         prev_lesson=prev_lesson,
                         next_lesson=next_lesson,
                         lesson_completed=lesson_completed,
                         enrollment=enrollment) # Pass enrollment to template

@app.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=lesson.course_id
    ).first_or_404()
    
    # Check if already completed
    existing_completion = LessonCompletion.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not existing_completion:
        completion = LessonCompletion(
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        db.session.add(completion)
        db.session.commit()
        
        # Calculate and update enrollment progress
        total_lessons = Lesson.query.filter_by(course_id=lesson.course_id).count()
        completed_lessons = LessonCompletion.query.join(Lesson).filter(
            LessonCompletion.user_id == current_user.id,
            Lesson.course_id == lesson.course_id
        ).count()
        
        enrollment.progress = (completed_lessons / total_lessons) * 100
        db.session.commit()
        
        flash('Lesson marked as complete!', 'success')
    else:
        flash('Lesson was already completed.', 'info')
    
    return redirect(url_for('view_lesson', lesson_id=lesson_id))

@app.route('/quiz/<int:lesson_id>')
@login_required
def take_quiz(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first_or_404()
    
    # Check if user is enrolled and has completed the lesson
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=lesson.course_id
    ).first_or_404()
    
    completion = LessonCompletion.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not completion:
        flash('Please complete the lesson before taking the quiz.', 'warning')
        return redirect(url_for('view_lesson', lesson_id=lesson_id))
    
    # Get user's previous attempts
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id
    ).order_by(QuizAttempt.completed_at.desc()).all()
    
    return render_template('quiz.html',
                         quiz=quiz,
                         lesson=lesson,
                         previous_attempts=previous_attempts)

@app.route('/quiz/<int:lesson_id>/submit', methods=['POST'])
@login_required
def submit_quiz(lesson_id):
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first_or_404()
    
    # Calculate score
    total_questions = len(quiz.questions)
    correct_answers = 0
    
    for question in quiz.questions:
        selected_option_id = request.form.get(f'question_{question.id}')
        if selected_option_id:
            selected_option = QuizOption.query.get(int(selected_option_id))
            if selected_option and selected_option.is_correct:
                correct_answers += 1
    
    score = (correct_answers / total_questions) * 100
    
    # Record attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score
    )
    db.session.add(attempt)
    db.session.commit()
    
    flash(f'Quiz submitted! Your score: {score:.1f}%', 'success')
    return redirect(url_for('take_quiz', lesson_id=lesson_id))

@app.route('/api/recommend', methods=['POST'])
@login_required
def recommend_courses():
    user_interests = request.json.get('interests', [])
    # Get courses user is not enrolled in
    enrolled_course_ids = [e.course_id for e in current_user.enrollments]
    
    # Semantic matching using RDF
    recommended = []
    for course in Course.query.filter(~Course.id.in_(enrolled_course_ids)).all():
        if any(interest in (course.semantic_tags or '').split(',') for interest in user_interests):
            recommended.append({
                'id': course.id,
                'title': course.title,
                'description': course.description
            })
    return jsonify(recommended)

@app.route('/api/learning-path', methods=['POST'])
@login_required
def create_learning_path():
    course_id = request.json.get('course_id')
    course = Course.query.get_or_404(course_id)
    
    # Create semantic relationships
    course_uri = ELEARN[f"course_{course_id}"]
    g.add((course_uri, RDF.type, ELEARN.Course))
    g.add((course_uri, RDFS.label, Literal(course.title)))
    
    # Generate adaptive learning path
    path = LearningPath(
        name=f"Path for {course.title}",
        prerequisites=course.semantic_tags,
        course_sequence=str([course_id]),
        user_id=current_user.id
    )
    db.session.add(path)
    db.session.commit()
    
    return jsonify({'path_id': path.id})

@app.route('/api/search')
def search_courses():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Search courses by title, description, and tags
    courses = Course.query.filter(
        db.or_(
            Course.title.ilike(f'%{query}%'),
            Course.description.ilike(f'%{query}%'),
            Course.semantic_tags.ilike(f'%{query}%')
        )
    ).all()
    
    return jsonify([{
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'tags': course.semantic_tags.split(',') if course.semantic_tags else [],
        'max_students': course.max_students,
        'duration_weeks': course.duration_weeks
    } for course in courses])

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']) and user.is_admin:
            login_user(user)
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('admin/login.html')

@app.route('/admin')
def admin_redirect():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    courses = Course.query.all()
    return render_template('admin/dashboard.html', courses=courses)

@app.route('/admin/course/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_course():
    if request.method == 'POST':
        course = Course(
            title=request.form['title'],
            description=request.form['description'],
            semantic_tags=request.form['tags'],
            max_students=int(request.form['max_students']),
            duration_weeks=int(request.form['duration_weeks'])
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/course_form.html', course=None)

@app.route('/admin/course/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.semantic_tags = request.form['tags']
        course.max_students = int(request.form['max_students'])
        course.duration_weeks = int(request.form['duration_weeks'])
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/course_form.html', course=course)

@app.route('/admin/course/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

def add_sample_courses():
    # Create admin user if none exists
    admin_email = 'bupechiyana11@gmail.com'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            username='Bupe Chiyana',
            email=admin_email,
            is_admin=True
        )
        admin.set_password('12345qwert')
        db.session.add(admin)
        # Commit admin user separately
        try:
            db.session.commit()
            print("Admin user created/verified.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding admin user: {e}")
            return # Stop if admin can't be added

    # --- Create Courses ---
    courses_data = [
        {'title': 'Introduction to Python', 'description': 'Learn Python programming from scratch', 'semantic_tags': 'programming,python,beginner', 'max_students': 50, 'duration_weeks': 8},
        {'title': 'Web Development Fundamentals', 'description': 'Master HTML, CSS, and JavaScript', 'semantic_tags': 'web,html,css,javascript', 'max_students': 40, 'duration_weeks': 10},
        {'title': 'Cloud Architecture and Design', 'description': 'Learn to design scalable and resilient cloud architectures using AWS, Azure, and GCP.', 'semantic_tags': 'cloud,aws,azure,gcp,architecture,infrastructure', 'max_students': 40, 'duration_weeks': 10},
        {'title': 'Advanced Cybersecurity', 'description': 'Master cybersecurity concepts, penetration testing, and security architecture.', 'semantic_tags': 'security,cybersecurity,pentest,networking,encryption', 'max_students': 35, 'duration_weeks': 12},
        {'title': 'Data Engineering Pipeline Design', 'description': 'Build robust data pipelines using modern tools and best practices.', 'semantic_tags': 'data,etl,python,sql,apache,spark,airflow', 'max_students': 45, 'duration_weeks': 8},
        {'title': 'Cross-Platform Mobile Development', 'description': 'Create mobile apps for iOS and Android using React Native and Flutter.', 'semantic_tags': 'mobile,react-native,flutter,ios,android,javascript', 'max_students': 50, 'duration_weeks': 10},
        {'title': 'DevOps and CI/CD', 'description': 'Implement DevOps practices and build CI/CD pipelines using modern tools.', 'semantic_tags': 'devops,ci-cd,jenkins,docker,kubernetes,git', 'max_students': 40, 'duration_weeks': 8},
        {'title': 'AI and Machine Learning Engineering', 'description': 'Design and deploy production-ready AI/ML systems at scale.', 'semantic_tags': 'ai,ml,python,tensorflow,pytorch,mlops', 'max_students': 35, 'duration_weeks': 14},
        {'title': 'Blockchain Development', 'description': 'Build decentralized applications and smart contracts on Ethereum and other platforms.', 'semantic_tags': 'blockchain,ethereum,solidity,web3,smart-contracts', 'max_students': 30, 'duration_weeks': 10},
        {'title': 'Microservices Architecture', 'description': 'Design and implement scalable microservices architectures using modern tools.', 'semantic_tags': 'microservices,architecture,docker,kubernetes,api,spring', 'max_students': 45, 'duration_weeks': 12}
    ]

    created_course_objects = []
    admin_user_id = admin.id if admin else 1 # Fallback to 1

    print("Checking and creating courses...")
    for course_data in courses_data:
        existing_course = Course.query.filter_by(title=course_data['title']).first()
        if not existing_course:
            course = Course(
                title=course_data['title'],
                description=course_data['description'],
                semantic_tags=course_data['semantic_tags'],
                user_id=admin_user_id,
                max_students=course_data['max_students'],
                duration_weeks=course_data['duration_weeks']
            )
            db.session.add(course)
            created_course_objects.append(course) # Add the object
            # print(f"  Added course '{course.title}' to session.") # Keep console cleaner
        else:
             created_course_objects.append(existing_course)
             # print(f"  Course '{course_data['title']}' already exists.")

    try:
        db.session.commit()
        print(f"Committed course additions/checks.")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing courses: {e}")
        return

    # --- Add Lessons and Quizzes for Each Course ---
    print("\nChecking and adding lessons/quizzes...")
    for course in created_course_objects:
        print(f"Processing course: {course.title} (ID: {course.id})")
        try:
            # Check if course already has 10 lessons
            lesson_count = Lesson.query.filter_by(course_id=course.id).count()
            if lesson_count >= 10:
                print(f"  Skipping: Course already has {lesson_count} lessons.")
                continue

            lessons_added_this_run = 0
            for i in range(1, 11):
                # Create Lesson
                lesson = Lesson(
                    title=f"{course.title} - Lesson {i}",
                    content=f"Placeholder content for Lesson {i} of {course.title}.\\n\\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum.",
                    lesson_number=i,
                    course_id=course.id
                )
                db.session.add(lesson)
                db.session.flush() # Need lesson ID for Quiz FK

                # Create Quiz for the Lesson
                quiz = Quiz(
                    title=f"Quiz for Lesson {i}",
                    lesson_id=lesson.id
                )
                db.session.add(quiz)
                db.session.flush() # Need quiz ID for Question FK

                # Create Quiz Questions
                for q_num in range(1, 3):
                    question = QuizQuestion(
                        quiz_id=quiz.id,
                        question_text=f"Placeholder Question {q_num} for Lesson {i} Quiz?"
                    )
                    db.session.add(question)
                    db.session.flush() # Need question ID for Option FK

                    # Create Quiz Options
                    for opt_num in range(1, 5):
                        option = QuizOption(
                            quiz_question_id=question.id,
                            option_text=f"Option {opt_num}",
                            is_correct=(opt_num == 1) # First option is correct
                        )
                        db.session.add(option)
                lessons_added_this_run += 1 # Increment after successful lesson/quiz/q/o creation

            # Commit after all lessons/quizzes for this specific course are added
            db.session.commit()
            print(f"  Successfully added {lessons_added_this_run} lessons/quizzes for course ID {course.id}.")

        except Exception as e:
            # Rollback changes for the current course if an error occurred
            db.session.rollback()
            print(f"  Error adding lessons/quizzes for course ID {course.id}: {e}")
            # Continue to the next course even if one fails
            continue

    print("\nFinished adding sample data.")

if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables if they don't exist...")
        db.create_all()
        print("Database tables checked/created.")
        
        # --- Optional: Seed Data --- 
        SEED_DATA = False # <-- CHANGE THIS TO True TO SEED
        
        if SEED_DATA:
            print("SEED_DATA is True. Attempting to add sample data...")
            add_sample_courses()
        else:
            print("SEED_DATA is False. Skipping add_sample_courses.")
        # --- End Optional Seed Data ---
            
    print("Starting Flask development server...")
    app.run(debug=True)
