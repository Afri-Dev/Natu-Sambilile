from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
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
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    semantic_tags = db.Column(db.String(500), nullable=False)
    max_students = db.Column(db.Integer, nullable=False)
    duration_weeks = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    prerequisites = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Course {self.title}>'

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
    enrollments = current_user.enrollments
    return render_template('my_courses.html', enrollments=enrollments)

@app.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first_or_404()
    
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
                         lesson_completed=lesson_completed)

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
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    # Search across title, description, and tags
    courses = Course.query.filter(
        (Course.title.ilike(f'%{query}%')) |
        (Course.description.ilike(f'%{query}%')) |
        (Course.semantic_tags.ilike(f'%{query}%'))
    ).all()

    # Add category information to search results
    return jsonify([{
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'category': course.category,
        'level': course.level,
        'tags': [tag.strip() for tag in course.semantic_tags.split(',') if tag.strip()],
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
        # Validate STEAM category
        allowed_categories = [
            'biology', 'chemistry', 'physics', 'astronomy', 'environmental',
            'programming', 'web_development', 'mobile_apps', 'ai_ml', 'cybersecurity',
            'mechanical', 'electrical', 'civil', 'chemical', 'aerospace',
            'digital_art', 'animation', 'graphic_design', 'game_design', 'music_production',
            'algebra', 'calculus', 'statistics', 'geometry', 'discrete_math'
        ]
        
        category = request.form.get('category')
        if not category or category not in allowed_categories:
            flash('Please select a valid STEAM category', 'error')
            return redirect(url_for('admin_add_course'))

        # Validate course level
        allowed_levels = ['beginner', 'intermediate', 'advanced']
        level = request.form.get('level')
        if not level or level not in allowed_levels:
            flash('Please select a valid course level', 'error')
            return redirect(url_for('admin_add_course'))

        # Validate max students (1-100)
        try:
            max_students = int(request.form['max_students'])
            if max_students < 1 or max_students > 100:
                flash('Maximum students must be between 1 and 100', 'error')
                return redirect(url_for('admin_add_course'))
        except (ValueError, TypeError):
            flash('Invalid value for maximum students', 'error')
            return redirect(url_for('admin_add_course'))

        # Validate duration (1-24 weeks)
        try:
            duration_weeks = int(request.form['duration_weeks'])
            if duration_weeks < 1 or duration_weeks > 24:
                flash('Course duration must be between 1 and 24 weeks', 'error')
                return redirect(url_for('admin_add_course'))
        except (ValueError, TypeError):
            flash('Invalid value for course duration', 'error')
            return redirect(url_for('admin_add_course'))

        # Create course
        course = Course(
            title=request.form['title'],
            description=request.form['description'],
            semantic_tags=request.form['tags'],
            max_students=max_students,
            duration_weeks=duration_weeks,
            category=category,
            level=level,
            prerequisites=request.form.get('prerequisites', '')
        )

        # Validate tags
        tags = [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        if not tags:
            flash('Please add at least one tag', 'error')
            return redirect(url_for('admin_add_course'))

        # Check if tags are STEAM-related
        steam_tags = [
            'programming', 'python', 'javascript', 'java', 'c++', 'data_structures', 'algorithms',
            'machine_learning', 'ai', 'neural_networks', 'deep_learning', 'cybersecurity', 'networking',
            'database', 'sql', 'web_development', 'frontend', 'backend', 'full_stack',
            'mobile_apps', 'android', 'ios', 'game_development', 'unity', 'unreal',
            'digital_art', 'graphic_design', 'animation', '3d_modeling', 'music_production',
            'mathematics', 'algebra', 'calculus', 'statistics', 'geometry',
            'physics', 'chemistry', 'biology', 'astronomy', 'environmental_science',
            'mechanical_engineering', 'electrical_engineering', 'civil_engineering', 'chemical_engineering', 'aerospace_engineering'
        ]

        non_steam_tags = [tag for tag in tags if tag.lower() not in steam_tags]
        if non_steam_tags:
            flash(f'Warning: Some tags are not STEAM-related: {", ".join(non_steam_tags)}', 'warning')

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
        # Same validation as add_course, but with existing course
        allowed_categories = [
            'biology', 'chemistry', 'physics', 'astronomy', 'environmental',
            'programming', 'web_development', 'mobile_apps', 'ai_ml', 'cybersecurity',
            'mechanical', 'electrical', 'civil', 'chemical', 'aerospace',
            'digital_art', 'animation', 'graphic_design', 'game_design', 'music_production',
            'algebra', 'calculus', 'statistics', 'geometry', 'discrete_math'
        ]
        
        category = request.form.get('category')
        if not category or category not in allowed_categories:
            flash('Please select a valid STEAM category', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        allowed_levels = ['beginner', 'intermediate', 'advanced']
        level = request.form.get('level')
        if not level or level not in allowed_levels:
            flash('Please select a valid course level', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        try:
            max_students = int(request.form['max_students'])
            if max_students < 1 or max_students > 100:
                flash('Maximum students must be between 1 and 100', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
        except (ValueError, TypeError):
            flash('Invalid value for maximum students', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        try:
            duration_weeks = int(request.form['duration_weeks'])
            if duration_weeks < 1 or duration_weeks > 24:
                flash('Course duration must be between 1 and 24 weeks', 'error')
                return redirect(url_for('admin_edit_course', course_id=course_id))
        except (ValueError, TypeError):
            flash('Invalid value for course duration', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        course.title = request.form['title']
        course.description = request.form['description']
        course.semantic_tags = request.form['tags']
        course.max_students = max_students
        course.duration_weeks = duration_weeks
        course.category = category
        course.level = level
        course.prerequisites = request.form.get('prerequisites', '')

        tags = [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        if not tags:
            flash('Please add at least one tag', 'error')
            return redirect(url_for('admin_edit_course', course_id=course_id))

        steam_tags = [
            'programming', 'python', 'javascript', 'java', 'c++', 'data_structures', 'algorithms',
            'machine_learning', 'ai', 'neural_networks', 'deep_learning', 'cybersecurity', 'networking',
            'database', 'sql', 'web_development', 'frontend', 'backend', 'full_stack',
            'mobile_apps', 'android', 'ios', 'game_development', 'unity', 'unreal',
            'digital_art', 'graphic_design', 'animation', '3d_modeling', 'music_production',
            'mathematics', 'algebra', 'calculus', 'statistics', 'geometry',
            'physics', 'chemistry', 'biology', 'astronomy', 'environmental_science',
            'mechanical_engineering', 'electrical_engineering', 'civil_engineering', 'chemical_engineering', 'aerospace_engineering'
        ]

        non_steam_tags = [tag for tag in tags if tag.lower() not in steam_tags]
        if non_steam_tags:
            flash(f'Warning: Some tags are not STEAM-related: {", ".join(non_steam_tags)}', 'warning')

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
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='Bupe Chiyana',
            email=admin_email,
            is_admin=True
        )
        admin.set_password('12345qwert')
        db.session.add(admin)
        db.session.commit()

    # Sample courses
    python_course = Course(
        title='Introduction to Python',
        description='Learn Python programming from scratch',
        semantic_tags='programming,python,beginner',
        user_id=1,
        max_students=50,
        duration_weeks=8,
        category='programming',
        level='beginner'
    )
    
    web_dev_course = Course(
        title='Web Development Fundamentals',
        description='Master HTML, CSS, and JavaScript',
        semantic_tags='web,html,css,javascript',
        user_id=1,
        max_students=40,
        duration_weeks=10,
        category='web_development',
        level='intermediate'
    )
    
    db.session.add(python_course)
    db.session.add(web_dev_course)
    db.session.commit()

    # Add new tech courses
    cloud_arch = Course(
        title='Cloud Architecture and Design',
        description='Learn to design scalable and resilient cloud architectures using AWS, Azure, and GCP.',
        semantic_tags='cloud,aws,azure,gcp,architecture,infrastructure',
        max_students=40,
        duration_weeks=10,
        category='programming',
        level='advanced'
    )
    db.session.add(cloud_arch)

    cybersecurity = Course(
        title='Advanced Cybersecurity',
        description='Master cybersecurity concepts, penetration testing, and security architecture.',
        semantic_tags='security,cybersecurity,pentest,networking,encryption',
        max_students=35,
        duration_weeks=12,
        category='cybersecurity',
        level='advanced'
    )
    db.session.add(cybersecurity)

    data_engineering = Course(
        title='Data Engineering Pipeline Design',
        description='Build robust data pipelines using modern tools and best practices.',
        semantic_tags='data,etl,python,sql,apache,spark,airflow',
        max_students=45,
        duration_weeks=8,
        category='programming',
        level='intermediate'
    )
    db.session.add(data_engineering)

    mobile_dev = Course(
        title='Cross-Platform Mobile Development',
        description='Create mobile apps for iOS and Android using React Native and Flutter.',
        semantic_tags='mobile,react-native,flutter,ios,android,javascript',
        max_students=50,
        duration_weeks=10,
        category='mobile_apps',
        level='intermediate'
    )
    db.session.add(mobile_dev)

    devops = Course(
        title='DevOps and CI/CD',
        description='Implement DevOps practices and build CI/CD pipelines using modern tools.',
        semantic_tags='devops,ci-cd,jenkins,docker,kubernetes,git',
        max_students=40,
        duration_weeks=8,
        category='programming',
        level='intermediate'
    )
    db.session.add(devops)

    ai_ml = Course(
        title='AI and Machine Learning Engineering',
        description='Design and deploy production-ready AI/ML systems at scale.',
        semantic_tags='ai,ml,python,tensorflow,pytorch,mlops',
        max_students=35,
        duration_weeks=14,
        category='ai_ml',
        level='advanced'
    )
    db.session.add(ai_ml)

    blockchain = Course(
        title='Blockchain Development',
        description='Build decentralized applications and smart contracts on Ethereum and other platforms.',
        semantic_tags='blockchain,ethereum,solidity,web3,smart-contracts',
        max_students=30,
        duration_weeks=10,
        category='programming',
        level='advanced'
    )
    db.session.add(blockchain)

    microservices = Course(
        title='Microservices Architecture',
        description='Design and implement scalable microservices architectures using modern tools.',
        semantic_tags='microservices,architecture,docker,kubernetes,api,spring',
        max_students=45,
        duration_weeks=12,
        category='programming',
        level='advanced'
    )
    db.session.add(microservices)

    db.session.commit()

    # Add lessons for Python course
    python_lessons = [
        {
            'title': 'Getting Started with Python',
            'content': '''
# Introduction to Python

Python is a high-level, interpreted programming language known for its simplicity and readability.

## In this lesson, you'll learn:
- What Python is and why it's popular
- How to install Python on your computer
- Writing your first Python program
- Basic Python syntax

## Your First Python Program

```python
print("Hello, World!")
```

This simple program demonstrates the basic syntax of Python. Let's break it down:
- `print()` is a built-in function
- The text inside the parentheses is called a "string"
- Strings can be enclosed in single or double quotes
''',
            'lesson_number': 1,
            'quiz': {
                'title': 'Python Basics Quiz',
                'questions': [
                    {
                        'text': 'What function is used to output text in Python?',
                        'options': [
                            {'text': 'print()', 'correct': True},
                            {'text': 'echo()', 'correct': False},
                            {'text': 'console.log()', 'correct': False},
                            {'text': 'write()', 'correct': False}
                        ]
                    },
                    {
                        'text': 'Which of these is a valid string in Python?',
                        'options': [
                            {'text': '"Hello World"', 'correct': True},
                            {'text': '<Hello World>', 'correct': False},
                            {'text': '[Hello World]', 'correct': False},
                            {'text': '{Hello World}', 'correct': False}
                        ]
                    }
                ]
            }
        },
        {
            'title': 'Variables and Data Types',
            'content': '''
# Variables and Data Types in Python

Variables are containers for storing data values. Python has several data types:

## Basic Data Types:
- Strings (text): `name = "John"`
- Integers (whole numbers): `age = 25`
- Floats (decimal numbers): `height = 1.75`
- Booleans (True/False): `is_student = True`

## Example:
```python
name = "Alice"
age = 30
height = 1.65
is_student = True

print(f"Name: {name}")
print(f"Age: {age}")
print(f"Height: {height}m")
print(f"Student: {is_student}")
```
''',
            'lesson_number': 2,
            'quiz': {
                'title': 'Data Types Quiz',
                'questions': [
                    {
                        'text': 'Which of these is a valid integer in Python?',
                        'options': [
                            {'text': '42', 'correct': True},
                            {'text': '"42"', 'correct': False},
                            {'text': '42.0', 'correct': False},
                            {'text': 'int(42)', 'correct': False}
                        ]
                    },
                    {
                        'text': 'What is the correct way to create a boolean variable?',
                        'options': [
                            {'text': 'is_valid = True', 'correct': True},
                            {'text': 'is_valid = "True"', 'correct': False},
                            {'text': 'is_valid = 1', 'correct': False},
                            {'text': 'is_valid = "yes"', 'correct': False}
                        ]
                    }
                ]
            }
        }
    ]

    # Add lessons for Web Development course
    web_lessons = [
        {
            'title': 'HTML Fundamentals',
            'content': '''
# Introduction to HTML

HTML (HyperText Markup Language) is the standard markup language for creating web pages.

## Basic HTML Structure:
```html
<!DOCTYPE html>
<html>
<head>
    <title>My First Webpage</title>
</head>
<body>
    <h1>Welcome to Web Development</h1>
    <p>This is a paragraph.</p>
</body>
</html>
```

## Common HTML Elements:
- Headings: `<h1>` to `<h6>`
- Paragraphs: `<p>`
- Links: `<a href="url">link text</a>`
- Images: `<img src="image.jpg" alt="description">`
''',
            'lesson_number': 1,
            'quiz': {
                'title': 'HTML Basics Quiz',
                'questions': [
                    {
                        'text': 'Which tag is used for the largest heading in HTML?',
                        'options': [
                            {'text': '<h1>', 'correct': True},
                            {'text': '<header>', 'correct': False},
                            {'text': '<heading>', 'correct': False},
                            {'text': '<h6>', 'correct': False}
                        ]
                    },
                    {
                        'text': 'What does HTML stand for?',
                        'options': [
                            {'text': 'HyperText Markup Language', 'correct': True},
                            {'text': 'High-Level Text Language', 'correct': False},
                            {'text': 'HyperTransfer Markup Language', 'correct': False},
                            {'text': 'Home Tool Markup Language', 'correct': False}
                        ]
                    }
                ]
            }
        },
        {
            'title': 'CSS Styling',
            'content': '''
# Introduction to CSS

CSS (Cascading Style Sheets) is used to style and layout web pages.

## Basic CSS Syntax:
```css
selector {
    property: value;
}
```

## Example:
```css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
    font-size: 24px;
}

.highlight {
    background-color: yellow;
}
```

## Ways to Add CSS:
1. Inline CSS
2. Internal CSS
3. External CSS
''',
            'lesson_number': 2,
            'quiz': {
                'title': 'CSS Fundamentals Quiz',
                'questions': [
                    {
                        'text': 'Which property is used to change text color in CSS?',
                        'options': [
                            {'text': 'color', 'correct': True},
                            {'text': 'text-color', 'correct': False},
                            {'text': 'font-color', 'correct': False},
                            {'text': 'text-style', 'correct': False}
                        ]
                    },
                    {
                        'text': 'What symbol is used to select elements by their class in CSS?',
                        'options': [
                            {'text': '.', 'correct': True},
                            {'text': '#', 'correct': False},
                            {'text': '@', 'correct': False},
                            {'text': '*', 'correct': False}
                        ]
                    }
                ]
            }
        }
    ]

    # Add Python lessons
    for lesson_data in python_lessons:
        lesson = Lesson(
            title=lesson_data['title'],
            content=lesson_data['content'],
            lesson_number=lesson_data['lesson_number'],
            course_id=python_course.id
        )
        db.session.add(lesson)
        db.session.commit()

        # Add quiz for the lesson
        quiz_data = lesson_data['quiz']
        quiz = Quiz(
            title=quiz_data['title'],
            lesson_id=lesson.id
        )
        db.session.add(quiz)
        db.session.commit()

        # Add questions and options
        for q_data in quiz_data['questions']:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data['text']
            )
            db.session.add(question)
            db.session.commit()

            for opt_data in q_data['options']:
                option = QuizOption(
                    quiz_question_id=question.id,
                    option_text=opt_data['text'],
                    is_correct=opt_data['correct']
                )
                db.session.add(option)

    # Add Web Development lessons
    for lesson_data in web_lessons:
        lesson = Lesson(
            title=lesson_data['title'],
            content=lesson_data['content'],
            lesson_number=lesson_data['lesson_number'],
            course_id=web_dev_course.id
        )
        db.session.add(lesson)
        db.session.commit()

        # Add quiz for the lesson
        quiz_data = lesson_data['quiz']
        quiz = Quiz(
            title=quiz_data['title'],
            lesson_id=lesson.id
        )
        db.session.add(quiz)
        db.session.commit()

        # Add questions and options
        for q_data in quiz_data['questions']:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data['text']
            )
            db.session.add(question)
            db.session.commit()

            for opt_data in q_data['options']:
                option = QuizOption(
                    quiz_question_id=question.id,
                    option_text=opt_data['text'],
                    is_correct=opt_data['correct']
                )
                db.session.add(option)

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        # Add sample courses
        add_sample_courses()
    app.run(debug=True)
