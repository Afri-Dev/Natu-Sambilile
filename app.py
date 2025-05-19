from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from datetime import datetime, timedelta
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.sql import func
import sqlite3
from sqlite3 import Error
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elearning.db'  # Using the database in the root directory
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

# Form classes
class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    video_url = URLField('Video URL', validators=[Optional(), URL()])
    resources = TextAreaField('Resources', validators=[Optional()])
    duration_minutes = IntegerField('Duration (minutes)', validators=[NumberRange(min=1)], default=60)
    submit = SubmitField('Save Lesson')

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Quiz')

class QuizQuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()])
    submit = SubmitField('Save Question')

# Form for quiz options
class QuizOptionForm(FlaskForm):
    option_text = TextAreaField('Option', validators=[DataRequired()])
    is_correct = BooleanField('Correct Answer')
    submit = SubmitField('Save Option')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, 
                                foreign_keys='Enrollment.user_id')

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
    enrollments = db.relationship('Enrollment', lazy=True)
    max_students = db.Column(db.Integer, default=50)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_weeks = db.Column(db.Integer, default=12)

class Enrollment(db.Model):
    """
    Enrollment model tracking student enrollment in courses.
    Establishes the many-to-many relationship between users and courses.
    """
    __tablename__ = 'enrollment'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='active', index=True)  # active, completed, dropped
    progress = db.Column(db.Float, default=0.0)  # 0 to 100
    
    # Define relationship to Course only, User relationship comes from backref
    # Removed the backref since it's already defined in Course model
    course = db.relationship('Course', lazy='joined')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),
        db.Index('idx_enrollment_status', 'status'),
    )
    
    def __repr__(self):
        """String representation of the enrollment"""
        return f"<Enrollment {self.id}: User {self.user_id} in Course {self.course_id}>"

class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prerequisites = db.Column(db.Text)
    course_sequence = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Lesson(db.Model):
    """
    Lesson model representing educational content within a course.
    Contains all information needed to display a lesson to a student.
    """
    __tablename__ = 'lesson'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    
    # Explicit relationship definition
    course = db.relationship('Course', backref=db.backref('lessons', 
                                                        lazy=True, 
                                                        order_by='Lesson.lesson_number'), 
                           lazy='joined')
    
    # These columns might not exist in the database yet
    video_url = db.Column(db.String(200), nullable=True)
    resources = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True, default=60)
    
    # Helper methods
    def get_duration(self):
        """Safe getter for duration_minutes with fallback"""
        return self.duration_minutes if self.duration_minutes is not None else 60
    
    def __repr__(self):
        """String representation of the lesson"""
        return f"<Lesson {self.id}: {self.title} (Course {self.course_id})>"

class LessonCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    """
    Quiz model representing a set of questions to test student knowledge.
    Each quiz is associated with a specific lesson.
    """
    __tablename__ = 'quiz'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False, index=True)
    
    # Define relationships explicitly
    lesson = db.relationship('Lesson', 
                          backref=db.backref('quiz', uselist=False, cascade="all, delete-orphan"), 
                          lazy='joined',
                          single_parent=True)
    questions = db.relationship('QuizQuestion', 
                             backref='quiz', 
                             lazy='select',
                             cascade="all, delete-orphan")
    attempts = db.relationship('QuizAttempt', 
                            backref='quiz', 
                            lazy='dynamic',
                            cascade="all, delete-orphan")
    
    def __repr__(self):
        """String representation of the quiz"""
        return f"<Quiz {self.id}: {self.title} for Lesson {self.lesson_id}>"

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
def inject_utility_functions():
    def get_lesson_duration(lesson):
        if hasattr(lesson, 'duration_minutes') and lesson.duration_minutes is not None:
            return lesson.duration_minutes
        return 60  # Default duration in minutes
        
    return {
        'now': datetime.utcnow,
        'get_lesson_duration': get_lesson_duration
    }

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
    search_query = request.args.get('q', '')
    
    query = Course.query
    if search_query:
        # Apply search filter similar to /api/search
        query = query.filter(
            db.or_(
                Course.title.ilike(f'%{search_query}%'),
                Course.description.ilike(f'%{search_query}%'),
                Course.semantic_tags.ilike(f'%{search_query}%')
            )
        )
        
    courses = query.all()
    
    # Get enrollment status for the potentially filtered courses
    user_enrollments = {e.course_id: e for e in current_user.enrollments if e.course_id in [c.id for c in courses]}
    
    return render_template('courses.html', 
                           courses=courses, 
                           user_enrollments=user_enrollments, 
                           search_query=search_query) # Pass the query to the template

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
    
    # Store user selections and correctness for each question
    questions_with_answers = []
    
    for question in quiz.questions:
        selected_option_id = request.form.get(f'question_{question.id}')
        is_correct = False
        
        if selected_option_id:
            selected_option = QuizOption.query.get(int(selected_option_id))
            if selected_option and selected_option.is_correct:
                correct_answers += 1
                is_correct = True
            
            questions_with_answers.append((question, selected_option, is_correct))
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Record attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Check if there's a next lesson
    lesson = Lesson.query.get_or_404(lesson_id)
    next_lesson = Lesson.query.filter_by(
        course_id=lesson.course_id,
        lesson_number=lesson.lesson_number + 1
    ).first()
    
    # Store in session for result page
    session['quiz_results'] = {
        'attempt_id': attempt.id,
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'questions_data': [(q.id, a.id if a else None, c) for q, a, c in questions_with_answers]
    }
    
    return render_template(
        'quiz_results.html',
        quiz=quiz,
        lesson=lesson,
        attempt=attempt,
        correct_answers=correct_answers,
        total_questions=total_questions,
        questions_with_answers=questions_with_answers,
        next_lesson=next_lesson
    )

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
    """
    Admin dashboard view showing platform statistics and recent activity.
    """
    # Get all required stats in a single query
    stats_query = db.session.query(
        db.func.count(db.distinct(Course.id)).label('total_courses'),
        db.func.count(db.distinct(User.id)).filter(User.is_admin == False).label('total_students'),
        db.func.count(Enrollment.id).label('total_enrollments'),
        db.func.count(db.case([(Enrollment.status == 'completed', 1)])).label('completed_enrollments')
    ).select_from(Enrollment)\
      .outerjoin(Course, Enrollment.course_id == Course.id)\
      .outerjoin(User, Enrollment.user_id == User.id)\
      .filter(User.is_admin == False)\
      .first()

    total_courses = stats_query.total_courses
    total_students = stats_query.total_students
    total_enrollments = stats_query.total_enrollments
    
    # Calculate completion rate
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = round((stats_query.completed_enrollments / total_enrollments) * 100)
    
    # Generate monthly enrollment data - use a single query with date filtering
    current_date = datetime.utcnow()
    start_date = current_date - timedelta(days=180)  # Last 6 months
    
    # Get monthly enrollments in a single query
    month_enrollments = db.session.query(
        db.func.strftime('%Y-%m', Enrollment.enrolled_at).label('month'),
        db.func.count().label('count')
    ).filter(
        Enrollment.enrolled_at >= start_date
    ).group_by('month').order_by('month').all()
    
    # Format for chart display
    monthly_enrollments = []
    for month_data in month_enrollments:
        year, month = month_data.month.split('-')
        month_name = datetime(int(year), int(month), 1).strftime('%b')
        monthly_enrollments.append({
            "month": month_name,
            "count": month_data.count
        })
    
    # Get courses with tags for category analysis
    courses = Course.query.filter(Course.semantic_tags != None).all()
    
    # Extract and count categories efficiently
    all_tags = []
    for course in courses:
        if course.semantic_tags:
            all_tags.extend([tag.strip() for tag in course.semantic_tags.split(',')])
    
    # Count and sort categories
    category_counts = {}
    for tag in all_tags:
        category_counts[tag] = category_counts.get(tag, 0) + 1
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    top_categories = dict(sorted_categories[:6])
    
    # Get recent activity with a single efficient query
    recent_enrollments = Enrollment.query.join(
        User, User.id == Enrollment.user_id
    ).join(
        Course, Course.id == Enrollment.course_id
    ).options(
        db.contains_eager(Enrollment.student),
        db.contains_eager(Enrollment.course)
    ).order_by(Enrollment.enrolled_at.desc()).limit(5).all()
    
    # Recent completions - more efficient query
    recent_completions = Enrollment.query.filter_by(status='completed').join(
        User, User.id == Enrollment.user_id
    ).join(
        Course, Course.id == Enrollment.course_id
    ).options(
        db.contains_eager(Enrollment.student),
        db.contains_eager(Enrollment.course)
    ).order_by(Enrollment.enrolled_at.desc()).limit(5).all()
    
    # Ensure default values for any missing data to prevent template errors
    if not monthly_enrollments:
        # Provide at least 6 months of empty data if no enrollments exist
        current = datetime.utcnow()
        for i in range(6, 0, -1):
            month_date = current - timedelta(days=30*i)
            monthly_enrollments.append({
                "month": month_date.strftime('%b'),
                "count": 0
            })
    
    # Format categories for proper display in the template
    categories_dict = {}
    for tag, count in category_counts.items():
        categories_dict[tag] = count
    
    # Prepare statistics with robust default values
    stats = {
        'total_courses': total_courses or 0,
        'total_students': total_students or 0,
        'enrollments': total_enrollments or 0,
        'completion_rate': completion_rate or 0,
        'monthly_enrollments': monthly_enrollments,
    }
    
    return render_template('admin/dashboard.html', 
                           stats=stats, 
                           courses=courses,
                           categories=categories_dict,
                           recent_enrollments=recent_enrollments,
                           recent_completions=recent_completions)

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

@app.route('/set-dark-mode', methods=['POST'])
def set_dark_mode():
    data = request.get_json()
    if data is None:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
        
    dark_mode_preference = data.get('dark_mode')
    if isinstance(dark_mode_preference, bool):
        session['dark_mode'] = dark_mode_preference
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid dark_mode value"}), 400

@app.route('/admin/courses/<int:course_id>/lessons')
@admin_required
def admin_course_lessons(course_id):
    """
    Display and manage lessons for a given course.
    
    Args:
        course_id: The ID of the course to display lessons for
    """
    course = Course.query.get_or_404(course_id)
    
    try:
        # Use a targeted query to avoid selecting problematic columns
        lesson_rows = db.session.query(
            Lesson.id, 
            Lesson.title, 
            Lesson.content, 
            Lesson.lesson_number, 
            Lesson.course_id
        ).filter(Lesson.course_id == course_id).order_by(Lesson.lesson_number).all()
        
        # Convert to proper Lesson objects with only necessary attributes
        lessons = []
        # Fetch all quiz associations at once for better performance
        quiz_mapping = {q.lesson_id: q for q in Quiz.query.filter(
            Quiz.lesson_id.in_([row.id for row in lesson_rows])
        ).all()}
        
        for row in lesson_rows:
            lesson = Lesson(
                id=row.id,
                title=row.title,
                content=row.content,
                lesson_number=row.lesson_number,
                course_id=row.course_id,
                video_url=None,
                resources=None,
                duration_minutes=60
            )
            # Set quiz from our preloaded mapping
            lesson.quiz = quiz_mapping.get(row.id)
            lessons.append(lesson)
    except Exception as e:
        # Fallback for any errors
        print(f"Error loading lessons: {e}")
        lessons = []
    
    return render_template('admin/course_lessons.html', course=course, lessons=lessons)

@app.route('/admin/lessons/new/<int:course_id>', methods=['GET', 'POST'])
@admin_required
def admin_new_lesson(course_id):
    """
    Create a new lesson for a course.
    
    Args:
        course_id: ID of the course to add a lesson to
    """
    course = Course.query.get_or_404(course_id)
    form = LessonForm()
    
    if form.validate_on_submit():
        # Find the highest lesson number for existing lessons
        highest_lesson_number = db.session.query(func.max(Lesson.lesson_number)).filter(Lesson.course_id == course_id).scalar() or 0
        
        # Create new lesson
        lesson = Lesson(
            title=form.title.data,
            content=form.content.data,
            video_url=form.video_url.data,
            resources=form.resources.data,
            duration_minutes=form.duration_minutes.data,
            course_id=course_id,
            lesson_number=highest_lesson_number + 1
        )
        
        db.session.add(lesson)
        db.session.commit()

        flash('Lesson created successfully!', 'success')
        return redirect(url_for('admin_course_lessons', course_id=course_id))
    
    return render_template('admin/lesson_form.html', form=form, course=course, course_id=course_id)

@app.route('/admin/lessons/edit/<int:lesson_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm(obj=lesson)
    
    if form.validate_on_submit():
        form.populate_obj(lesson)
        db.session.commit()
        
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('admin_course_lessons', course_id=lesson.course_id))
    
    return render_template('admin/lesson_form.html', form=form, lesson=lesson, course=lesson.course)

@app.route('/admin/lessons/delete/<int:lesson_id>', methods=['POST'])
@admin_required
def admin_delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    
    # Delete any quizzes associated with this lesson
    quizzes = Quiz.query.filter_by(lesson_id=lesson_id).all()
    for quiz in quizzes:
        # Delete quiz questions and options
        questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
        for question in questions:
            QuizOption.query.filter_by(question_id=question.id).delete()
        
        QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
    
    Quiz.query.filter_by(lesson_id=lesson_id).delete()
    
    # Delete the lesson
    db.session.delete(lesson)
    
    # Reorder the remaining lessons
    remaining_lessons = Lesson.query.filter_by(course_id=course_id).filter(Lesson.id != lesson_id).order_by(Lesson.lesson_number).all()
    for i, lesson in enumerate(remaining_lessons):
        lesson.lesson_number = i + 1
    
    db.session.commit()
    
    flash('Lesson and associated quizzes deleted successfully!', 'success')
    return redirect(url_for('admin_course_lessons', course_id=course_id))

@app.route('/admin/lessons/<int:lesson_id>/reorder', methods=['POST'])
@admin_required
def admin_reorder_lesson(lesson_id):
    """
    Reorder lessons for a course by moving a lesson up or down.
    
    Args:
        lesson_id: ID of the lesson to reorder
        
    Returns:
        JSON response with success status and message
    """
    lesson = Lesson.query.get_or_404(lesson_id)
    direction = request.json.get('direction')
    course_id = request.json.get('course_id') or lesson.course_id
    
    # Get all lessons for this course ordered by lesson_number
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_number).all()
    
    # Find current position
    current_position = None
    for i, l in enumerate(lessons):
        if l.id == lesson_id:
            current_position = i
            break
    
    if current_position is None:
        return jsonify({'success': False, 'message': 'Lesson not found in course'})
    
    # Calculate target position
    if direction == 'up' and current_position > 0:
        target_position = current_position - 1
    elif direction == 'down' and current_position < len(lessons) - 1:
        target_position = current_position + 1
    else:
        return jsonify({'success': False, 'message': 'Cannot move lesson further'})
    
    # Swap lesson_number values
    current_lesson_number = lesson.lesson_number
    target_lesson = lessons[target_position]
    target_lesson_number = target_lesson.lesson_number
    
    lesson.lesson_number = target_lesson_number
    target_lesson.lesson_number = current_lesson_number
    
    db.session.commit()

    return jsonify({'success': True, 'message': f'Lesson moved {direction} successfully'})

@app.route('/admin/quizzes/new/<int:lesson_id>', methods=['GET', 'POST'])
@admin_required
def admin_new_quiz(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if a quiz already exists for this lesson
    existing_quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
    if existing_quiz:
        flash('A quiz already exists for this lesson. Please edit the existing quiz.', 'warning')
        return redirect(url_for('admin_edit_quiz', quiz_id=existing_quiz.id))
    
    form = QuizForm()
    
    if form.validate_on_submit():
        # Create new quiz
        quiz = Quiz(
            title=form.title.data,
            lesson_id=lesson_id
        )
        db.session.add(quiz)
        db.session.commit()

        flash('Quiz created successfully! Now add some questions.', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=quiz.id))
    
    return render_template('admin/quiz_form.html', form=form, lesson=lesson)

@app.route('/admin/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm(obj=quiz)
    
    if form.validate_on_submit():
        form.populate_obj(quiz)
        db.session.commit()

        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('admin_course_lessons', course_id=quiz.lesson.course_id))
    
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    for question in questions:
        question.options = QuizOption.query.filter_by(quiz_question_id=question.id).all()
    
    return render_template('admin/quiz_form.html', form=form, quiz=quiz, questions=questions, lesson=quiz.lesson)

@app.route('/admin/quizzes/delete/<int:quiz_id>', methods=['POST'])
@admin_required
def admin_delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    lesson_id = quiz.lesson_id
    course_id = Lesson.query.get(lesson_id).course_id
    
    # Delete quiz questions and options
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
    for question in questions:
        QuizOption.query.filter_by(question_id=question.id).delete()
    
    QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
    
    # Delete the quiz
    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin_course_lessons', course_id=course_id))

@app.route('/admin/quizzes/<int:quiz_id>/questions/new', methods=['GET', 'POST'])
@admin_required
def admin_new_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizQuestionForm()
    
    if form.validate_on_submit():
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=form.question_text.data
        )
        db.session.add(question)
        db.session.commit()

        flash('Question added successfully! Now add some options.', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=quiz_id))
    
    return render_template('admin/question_form.html', form=form, quiz=quiz)

@app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_question(question_id):
    question = QuizQuestion.query.get_or_404(question_id)
    form = QuizQuestionForm(obj=question)
    
    if form.validate_on_submit():
        form.populate_obj(question)
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=question.quiz_id))
    
    return render_template('admin/question_form.html', form=form, question=question, quiz=question.quiz)

@app.route('/admin/questions/<int:question_id>/options/new', methods=['GET', 'POST'])
@admin_required
def admin_new_option(question_id):
    question = QuizQuestion.query.get_or_404(question_id)
    form = QuizOptionForm()
    
    if form.validate_on_submit():
        option = QuizOption(
            quiz_question_id=question_id,
            option_text=form.option_text.data,
            is_correct=form.is_correct.data
        )
        db.session.add(option)
        db.session.commit()
        
        flash('Option added successfully!', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=question.quiz_id))
    
    return render_template('admin/option_form.html', form=form, question=question)

@app.route('/admin/options/<int:option_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_option(option_id):
    option = QuizOption.query.get_or_404(option_id)
    form = QuizOptionForm(obj=option)
    
    if form.validate_on_submit():
        form.populate_obj(option)
        db.session.commit()
        
        flash('Option updated successfully!', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=option.question.quiz_id))
    
    return render_template('admin/option_form.html', form=form, option=option, question=option.question)

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@admin_required
def admin_delete_question(question_id):
    question = QuizQuestion.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    
    # Delete options first
    QuizOption.query.filter_by(quiz_question_id=question_id).delete()
    
    # Delete question
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_edit_quiz', quiz_id=quiz_id))

@app.route('/admin/options/<int:option_id>/delete', methods=['POST'])
@admin_required
def admin_delete_option(option_id):
    option = QuizOption.query.get_or_404(option_id)
    question = option.question
    
    db.session.delete(option)
    db.session.commit()
    
    flash('Option deleted successfully!', 'success')
    return redirect(url_for('admin_edit_quiz', quiz_id=question.quiz_id))

@app.route('/quiz/results/<int:attempt_id>')
@login_required
def view_quiz_results(attempt_id):
    # Get the attempt
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    quiz = Quiz.query.get_or_404(attempt.quiz_id)
    lesson = Lesson.query.filter_by(id=quiz.lesson_id).first_or_404()
    
    # Check if this quiz belongs to a course the user is enrolled in
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=lesson.course_id
    ).first_or_404()
    
    # Check if there's a next lesson
    next_lesson = Lesson.query.filter_by(
        course_id=lesson.course_id,
        lesson_number=lesson.lesson_number + 1
    ).first()
    
    # If we have stored results in the session, use them
    if 'quiz_results' in session and session['quiz_results']['attempt_id'] == attempt_id:
        correct_answers = session['quiz_results']['correct_answers']
        total_questions = session['quiz_results']['total_questions']
        
        # Reconstruct questions with answers
        questions_with_answers = []
        for question_id, option_id, is_correct in session['quiz_results']['questions_data']:
            question = QuizQuestion.query.get(question_id)
            option = QuizOption.query.get(option_id) if option_id else None
            questions_with_answers.append((question, option, is_correct))
    else:
        # Otherwise reconstruct from the database
        questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
        total_questions = len(questions)
        
        # We don't store actual answers in the database, so we'll do our best estimate
        # based on the score
        correct_answers = int((attempt.score / 100) * total_questions)
        
        # Just show questions without specific user answers
        questions_with_answers = []
        for question in questions:
            # Get all options
            question.options = QuizOption.query.filter_by(quiz_question_id=question.id).all()
            # Find the correct option
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            questions_with_answers.append((question, correct_option, True))
    
    return render_template(
        'quiz_results.html',
        quiz=quiz,
        lesson=lesson,
        attempt=attempt,
        correct_answers=correct_answers,
        total_questions=total_questions,
        questions_with_answers=questions_with_answers,
        next_lesson=next_lesson
    )

@app.route('/admin/quizzes/<int:quiz_id>/attempts')
@admin_required
def admin_quiz_attempts(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    lesson = Lesson.query.get_or_404(quiz.lesson_id)
    course = Course.query.get_or_404(lesson.course_id)
    
    # Get all attempts for this quiz, ordered by completion date (newest first)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Preload users for all attempts
    user_ids = [attempt.user_id for attempt in attempts]
    users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()}
    
    # Calculate statistics
    total_attempts = len(attempts)
    avg_score = sum(attempt.score for attempt in attempts) / total_attempts if total_attempts > 0 else 0
    passing_attempts = sum(1 for attempt in attempts if attempt.score >= 70)
    pass_rate = (passing_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Group attempts by user for the leaderboard
    user_best_attempts = {}
    for attempt in attempts:
        user_id = attempt.user_id
        if user_id not in user_best_attempts or attempt.score > user_best_attempts[user_id].score:
            user_best_attempts[user_id] = attempt
    
    # Sort the leaderboard by score (highest first)
    leaderboard = sorted(user_best_attempts.values(), key=lambda x: x.score, reverse=True)
    
    return render_template(
        'admin/quiz_attempts.html',
        quiz=quiz,
        lesson=lesson,
        course=course,
        attempts=attempts,
        users=users,
        stats={
            'total_attempts': total_attempts,
            'avg_score': avg_score,
            'passing_attempts': passing_attempts,
            'pass_rate': pass_rate
        },
        leaderboard=leaderboard
    )

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Add sample data if enabled
        SEED_DATA = False  # <-- CHANGE THIS TO True TO SEED
        
        if SEED_DATA:
            from utils.db_sample_data import add_sample_data
            print("SEED_DATA is True. Attempting to add sample data...")
            add_sample_data()
        else:
            print("SEED_DATA is False. Skipping sample data creation.")
    
    # Run the app
    app.run(debug=True)
