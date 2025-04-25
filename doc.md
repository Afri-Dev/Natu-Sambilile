# LearnHub Platform Documentation

## 1. Overview

LearnHub is a comprehensive learning management system designed to provide a seamless educational experience for both administrators and students. The platform enables course creation, student enrollment, content management, quiz administration, and progress tracking in a modern, responsive interface.

The application follows an MVC (Model-View-Controller) architecture using Flask as the web framework:
- **Models**: SQLAlchemy ORM classes representing database entities
- **Views**: Jinja2 templates rendering HTML interfaces
- **Controllers**: Flask route functions handling business logic

## 2. Technology Stack

- **Backend**: Python 3.x with Flask framework
- **Database**: SQLAlchemy ORM with SQLite for development (configurable for production databases)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **CSS Framework**: TailwindCSS with custom components defined in modern-ui.css
- **JavaScript Libraries**: 
  - Chart.js for data visualization
  - SortableJS for drag-and-drop functionality
- **Icons**: Font Awesome 5
- **Authentication**: Flask-Login for session management
- **Form Handling**: Flask-WTF with CSRF protection

## 3. Application Structure

```
LearnHub/
├── app.py                # Main application file with routes and models
├── static/               # Static assets
│   ├── css/              
│   │   └── modern-ui.css # Custom UI components and styling
│   ├── js/
│   │   └── dashboard-charts.js # Chart visualizations
│   └── images/           # Image assets for the platform
├── templates/            # HTML templates
│   ├── admin/            # Admin interface templates
│   │   ├── admin_base.html    # Base template for admin pages
│   │   ├── dashboard.html     # Admin dashboard
│   │   ├── login.html         # Admin login
│   │   ├── course_form.html   # Course creation/editing
│   │   ├── course_lessons.html # Course lessons management
│   │   └── quiz_form.html     # Quiz creation/editing
│   ├── auth/             # Authentication templates
│   │   ├── login.html    # User login
│   │   └── signup.html   # User registration
│   ├── student/          # Student interface templates
│   │   ├── dashboard.html     # Student dashboard
│   │   ├── course_details.html # Course information
│   │   └── lesson_view.html   # Lesson content display
│   ├── base.html         # Base template for student pages
│   └── index.html        # Landing page
├── config.py             # Configuration settings
├── requirements.txt      # Package dependencies
└── README.md             # Project documentation
```

## 4. Database Models

The application uses SQLAlchemy ORM to define the database schema and relationships between entities. Each model represents a table in the database.

### User Model
Manages user accounts with different permission levels.

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    enrollments = db.relationship('Enrollment', back_populates='student')
    learning_paths = db.relationship('LearningPath', secondary='user_learning_paths')
```

**Logic**:
- Handles password hashing and verification
- Tracks user role (admin vs. student)
- Manages relationships with courses through enrollments
- Supports learning path assignments

### Course Model
Represents educational courses offered on the platform.

```python
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    duration_weeks = db.Column(db.Integer, default=4)
    max_students = db.Column(db.Integer, default=30)
    semantic_tags = db.Column(db.String(200))  # Comma-separated tags
    
    # Relationships
    instructor = db.relationship('User')
    enrollments = db.relationship('Enrollment', back_populates='course')
    lessons = db.relationship('Lesson', back_populates='course', order_by='Lesson.order_index')
    quizzes = db.relationship('Quiz', back_populates='course')
```

**Logic**:
- Stores course metadata and content structure
- Manages enrollment capacity with max_students
- Tracks course duration and categorization
- Maintains relationships with lessons, quizzes, and enrollments

### Enrollment Model
Tracks student enrollments in courses.

```python
class Enrollment(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')
    
    # Constraints
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)
```

**Logic**:
- Implements a many-to-many relationship between users and courses
- Tracks enrollment dates and completion status
- Ensures uniqueness to prevent duplicate enrollments
- Calculates progress through related lesson completions

### Lesson Model
Stores course content organized in lessons.

```python
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='lessons')
    completions = db.relationship('LessonCompletion', back_populates='lesson')
```

**Logic**:
- Organizes course content in sequential order
- Supports rich text content storage
- Manages display order through order_index
- Tracks which students have completed the lesson

### LessonCompletion Model
Tracks which lessons students have completed.

```python
class LessonCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    lesson = db.relationship('Lesson', back_populates='completions')
    
    # Constraints
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)
```

**Logic**:
- Records when a student completes a lesson
- Ensures each lesson is only marked complete once per student
- Used to calculate overall course progress

### Quiz Model
Manages assessment quizzes attached to courses.

```python
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    passing_percentage = db.Column(db.Integer, default=70)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='quizzes')
    questions = db.relationship('QuizQuestion', back_populates='quiz', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', back_populates='quiz')
```

**Logic**:
- Defines assessment criteria for a course
- Sets passing threshold for student success
- Manages collection of questions
- Tracks student attempts and performance

### QuizQuestion Model
Stores quiz questions with multiple choice options.

```python
class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0)
    
    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    options = db.relationship('QuizOption', back_populates='question', cascade='all, delete-orphan')
```

**Logic**:
- Stores the question text and display order
- Links to possible answer options
- Belongs to a specific quiz
- Manages cascading deletion of options

### QuizOption Model
Represents answer options for quiz questions.

```python
class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    # Relationships
    question = db.relationship('QuizQuestion', back_populates='options')
```

**Logic**:
- Defines possible answers for a question
- Marks which option is correct
- Used in scoring quiz attempts

### QuizAttempt Model
Records student quiz attempts and scores.

```python
class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Float)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_passed = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User')
    quiz = db.relationship('Quiz', back_populates='attempts')
```

**Logic**:
- Tracks when a student starts and completes a quiz
- Calculates and stores the score as a percentage
- Determines pass/fail status based on quiz passing_percentage
- Used in course completion calculations

### LearningPath Model
Organizes courses into structured learning paths.

```python
class LearningPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary='user_learning_paths')
    courses = db.relationship('Course', secondary='learning_path_courses')
```

**Logic**:
- Groups related courses into a structured sequence
- Assigns learning paths to students
- Tracks progress across multiple courses
- Provides guided learning experiences

## 5. Key Features and Application Logic

### Admin Dashboard
- **Platform Statistics**: Real-time metrics on courses, students, enrollments, and completion rates
- **Enrollment Trends**: Time-series visualization of student acquisitions
- **Category Distribution**: Analysis of course topics and their popularity
- **Recent Activity**: Monitoring of platform events like enrollments and completions
- **Course Management**: Comprehensive tools for CRUD operations on courses

### Course Management
- **Course Creation Workflow**: Structured process for course development
- **Lesson Sequencing**: Ordering and organization of educational content
- **Quiz Integration**: Assessment tools tied to specific courses
- **Enrollment Monitoring**: Tracking student participation and progress
- **Category Management**: Classification and tagging system for courses

### Student Experience
- **Personalized Dashboard**: Customized view of enrolled courses and progress
- **Course Discovery**: Browsing and search functionality for available courses
- **Learning Path**: Structured sequences of courses for comprehensive learning
- **Progress Tracking**: Visual indicators of completion status
- **Assessment System**: Quiz taking and result feedback

### Authentication & Authorization
- **Role-Based Access**: Different interfaces and permissions for students and admins
- **Secure Authentication**: Password hashing and session management
- **Protected Routes**: Middleware to control access to sensitive functions
- **Account Management**: Profile editing and password reset functionality

## 6. Route Functions and Application Logic

### Authentication Routes

#### `@app.route('/signup', methods=['GET', 'POST'])`
**Function**: `signup()`

**Logic**:
1. Presents registration form on GET request
2. Validates submitted data on POST request
3. Checks for existing username or email
4. Creates new user with hashed password
5. Redirects to login page with success message

```python
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/signup.html')
```

#### `@app.route('/login', methods=['GET', 'POST'])`
**Function**: `login()`

**Logic**:
1. Presents login form on GET request
2. Validates credentials on POST request
3. Checks if user exists and password is correct
4. Creates session for authenticated user
5. Redirects to appropriate dashboard based on role

```python
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
        
        # Set session variables
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html')
```

#### `@app.route('/admin/login', methods=['GET', 'POST'])`
**Function**: `admin_login()`

**Logic**:
1. Specialized login form for administrators
2. Validates credentials and admin status
3. Redirects to admin dashboard on success
4. Provides security by checking admin flag

```python
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password) or not user.is_admin:
            flash('Invalid credentials or insufficient permissions', 'error')
            return redirect(url_for('admin_login'))
        
        # Set session variables
        session['user_id'] = user.id
        session['is_admin'] = True
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/login.html')
```

#### `@app.route('/logout')`
**Function**: `logout()`

**Logic**:
1. Clears user session data
2. Redirects to login page with message

```python
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))
```

### Admin Routes

#### `@app.route('/admin/dashboard')`
**Function**: `admin_dashboard()`

**Logic**:
1. Verifies admin privileges
2. Calculates platform statistics:
   - Total courses and students
   - Enrollment counts and completion rates
   - Recent activity
3. Extracts categories from course tags
4. Prepares data for visualization charts
5. Renders dashboard template with context data

```python
def admin_dashboard():
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    # Get basic statistics
    total_courses = Course.query.count()
    total_students = User.query.filter_by(is_admin=False).count()
    enrollments = Enrollment.query.count()
    
    # Calculate completion rate
    completed = Enrollment.query.filter_by(is_completed=True).count()
    completion_rate = (completed / enrollments * 100) if enrollments > 0 else 0
    
    # Get recent enrollments
    recent_enrollments = db.session.query(Enrollment).\
        join(User, User.id == Enrollment.user_id).\
        join(Course, Course.id == Enrollment.course_id).\
        options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.course)
        ).\
        order_by(Enrollment.enrolled_at.desc()).\
        limit(5).all()
    
    # Get recent completions
    recent_completions = db.session.query(Enrollment).\
        filter_by(is_completed=True).\
        join(User, User.id == Enrollment.user_id).\
        join(Course, Course.id == Enrollment.course_id).\
        options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.course)
        ).\
        order_by(Enrollment.completed_at.desc()).\
        limit(5).all()
    
    # Extract categories from course tags
    all_tags = []
    for course in Course.query.all():
        if course.semantic_tags:
            all_tags.extend([tag.strip() for tag in course.semantic_tags.split(',')])
    
    # Count occurrences of each category
    categories = {}
    for tag in all_tags:
        if tag in categories:
            categories[tag] += 1
        else:
            categories[tag] = 1
    
    # Sort categories by count, descending
    categories = dict(sorted(categories.items(), key=lambda item: item[1], reverse=True))
    
    # Prepare monthly enrollment data for chart
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Query enrollments by month
    enrollments_by_month = db.session.query(
        func.date_format(Enrollment.enrolled_at, '%Y-%m').label('month'),
        func.count().label('count')
    ).filter(Enrollment.enrolled_at >= six_months_ago).\
    group_by('month').\
    order_by('month').\
    all()
    
    # Format data for chart.js
    monthly_enrollments = [
        {'month': result.month, 'count': result.count}
        for result in enrollments_by_month
    ]
    
    # Compile all statistics
    stats = {
        'total_courses': total_courses,
        'total_students': total_students,
        'enrollments': enrollments,
        'completion_rate': completion_rate,
        'monthly_enrollments': monthly_enrollments
    }
    
    # Get all courses for the management table
    courses = Course.query.all()
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        categories=categories,
        recent_enrollments=recent_enrollments,
        recent_completions=recent_completions,
        courses=courses
    )
```

#### `@app.route('/admin/courses/add', methods=['GET', 'POST'])`
**Function**: `admin_add_course()`

**Logic**:
1. Presents course creation form on GET request
2. Validates submitted data on POST request
3. Creates new course record with form data
4. Handles file upload for course image
5. Redirects to course management with success message

```python
def admin_add_course():
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration_weeks = int(request.form['duration_weeks'])
        max_students = int(request.form['max_students'])
        semantic_tags = request.form['semantic_tags']
        
        # Handle image upload
        image_url = None
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            # Generate secure filename
            filename = secure_filename(image.filename)
            # Create unique filename with timestamp
            unique_filename = f"{int(time.time())}_{filename}"
            # Save file
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            # Set URL for database
            image_url = f"/static/uploads/{unique_filename}"
        
        # Create new course
        new_course = Course(
            title=title,
            description=description,
            image_url=image_url,
            instructor_id=session['user_id'],
            duration_weeks=duration_weeks,
            max_students=max_students,
            semantic_tags=semantic_tags
        )
        
        db.session.add(new_course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/course_form.html', course=None)
```

#### `@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])`
**Function**: `admin_edit_course(course_id)`

**Logic**:
1. Retrieves existing course data for editing
2. Populates form with current values
3. Updates record with submitted changes
4. Handles image replacement if new file uploaded
5. Returns to course management on completion

```python
def admin_edit_course(course_id):
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.duration_weeks = int(request.form['duration_weeks'])
        course.max_students = int(request.form['max_students'])
        course.semantic_tags = request.form['semantic_tags']
        
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            # Generate secure filename
            filename = secure_filename(image.filename)
            # Create unique filename with timestamp
            unique_filename = f"{int(time.time())}_{filename}"
            # Save file
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            # Set URL for database
            course.image_url = f"/static/uploads/{unique_filename}"
        
        course.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/course_form.html', course=course)
```

#### `@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])`
**Function**: `admin_delete_course(course_id)`

**Logic**:
1. Confirms admin privileges
2. Retrieves course by ID
3. Cascades deletion to related records (enrollments, lessons, quizzes)
4. Removes course from database
5. Returns to course management with confirmation

```python
def admin_delete_course(course_id):
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    course = Course.query.get_or_404(course_id)
    
    # Delete course (cascade will handle related records)
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))
```

#### `@app.route('/admin/courses/<int:course_id>/lessons', methods=['GET', 'POST'])`
**Function**: `admin_course_lessons(course_id)`

**Logic**:
1. Displays lesson management interface for specific course
2. Lists existing lessons in order
3. Provides form for adding new lessons
4. Handles lesson reordering through AJAX requests
5. Allows editing and deletion of lessons

```python
def admin_course_lessons(course_id):
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_lesson':
            title = request.form['title']
            content = request.form['content']
            
            # Get max order_index and add 1
            max_order = db.session.query(func.max(Lesson.order_index)).\
                filter(Lesson.course_id == course_id).scalar() or -1
            
            new_lesson = Lesson(
                course_id=course_id,
                title=title,
                content=content,
                order_index=max_order + 1
            )
            
            db.session.add(new_lesson)
            db.session.commit()
            
            flash('Lesson added successfully!', 'success')
            return redirect(url_for('admin_course_lessons', course_id=course_id))
        
        elif action == 'update_order':
            # Handle AJAX lesson reordering
            lesson_order = request.json.get('lesson_order')
            for i, lesson_id in enumerate(lesson_order):
                lesson = Lesson.query.get(lesson_id)
                if lesson and lesson.course_id == course_id:
                    lesson.order_index = i
            
            db.session.commit()
            return jsonify({'status': 'success'})
        
        elif action == 'edit_lesson':
            lesson_id = int(request.form['lesson_id'])
            lesson = Lesson.query.get_or_404(lesson_id)
            
            if lesson.course_id != course_id:
                flash('Unauthorized access to lesson', 'error')
                return redirect(url_for('admin_course_lessons', course_id=course_id))
            
            lesson.title = request.form['title']
            lesson.content = request.form['content']
            lesson.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Lesson updated successfully!', 'success')
            return redirect(url_for('admin_course_lessons', course_id=course_id))
        
        elif action == 'delete_lesson':
            lesson_id = int(request.form['lesson_id'])
            lesson = Lesson.query.get_or_404(lesson_id)
            
            if lesson.course_id != course_id:
                flash('Unauthorized access to lesson', 'error')
                return redirect(url_for('admin_course_lessons', course_id=course_id))
            
            # Delete the lesson
            db.session.delete(lesson)
            
            # Reorder remaining lessons
            remaining_lessons = Lesson.query.filter_by(course_id=course_id).\
                filter(Lesson.id != lesson_id).\
                order_by(Lesson.order_index).all()
            
            for i, l in enumerate(remaining_lessons):
                l.order_index = i
            
            db.session.commit()
            
            flash('Lesson deleted successfully!', 'success')
            return redirect(url_for('admin_course_lessons', course_id=course_id))
    
    return render_template('admin/course_lessons.html', course=course, lessons=lessons)
```

#### `@app.route('/admin/quizzes/create', methods=['GET', 'POST'])`
**Function**: `admin_create_quiz()`

**Logic**:
1. Presents quiz creation form
2. Allows selection of associated course
3. Processes basic quiz metadata
4. Creates initial quiz structure
5. Redirects to question management

```python
def admin_create_quiz():
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    # Get all courses for the dropdown
    courses = Course.query.all()
    
    if request.method == 'POST':
        course_id = int(request.form['course_id'])
        title = request.form['title']
        description = request.form['description']
        passing_percentage = int(request.form['passing_percentage'])
        
        # Create new quiz
        new_quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description,
            passing_percentage=passing_percentage
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        flash('Quiz created! Now add questions.', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=new_quiz.id))
    
    return render_template('admin/quiz_form.html', courses=courses, quiz=None)
```

#### `@app.route('/admin/quizzes/<int:quiz_id>/questions/add', methods=['POST'])`
**Function**: `admin_new_question(quiz_id)`

**Logic**:
1. Processes new question submission
2. Validates question text and options
3. Ensures at least one correct answer
4. Adds question and options to database
5. Returns to quiz editor

```python
def admin_new_question(quiz_id):
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        
        # Get max order_index and add 1
        max_order = db.session.query(func.max(QuizQuestion.order_index)).\
            filter(QuizQuestion.quiz_id == quiz_id).scalar() or -1
        
        # Create new question
        new_question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            order_index=max_order + 1
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        # Process options
        option_texts = request.form.getlist('option_text[]')
        is_correct_values = request.form.getlist('is_correct[]')
        
        for i, option_text in enumerate(option_texts):
            if option_text.strip():  # Skip empty options
                is_correct = str(i) in is_correct_values
                
                option = QuizOption(
                    question_id=new_question.id,
                    option_text=option_text,
                    is_correct=is_correct
                )
                
                db.session.add(option)
        
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_edit_quiz', quiz_id=quiz_id))
    
    flash('Invalid request', 'error')
    return redirect(url_for('admin_edit_quiz', quiz_id=quiz_id))
``` 