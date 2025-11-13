"""
Wajina Suite - School Management System
Wajina International School, Makurdi
"""

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from database import db
from sqlalchemy import text
import os

# Initialize Flask app
app = Flask(__name__)
# Use environment variable for secret key in production, fallback to default for development
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'wajina-suite-secret-key-2024')

# Database configuration - handle both SQLite and PostgreSQL
database_url = os.environ.get('DATABASE_URL', 'sqlite:///wajina_suite.db')
# Convert postgres:// to postgresql:// for SQLAlchemy compatibility
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# App Settings (defaults)
app.config['SCHOOL_NAME'] = 'Wajina International School'
app.config['SCHOOL_ADDRESS'] = 'Makurdi, Benue State, Nigeria'
app.config['SCHOOL_PHONE'] = ''
app.config['SCHOOL_EMAIL'] = ''
app.config['SCHOOL_WEBSITE'] = ''
app.config['SCHOOL_LOGO'] = ''  # Path to school logo
app.config['CURRENT_SESSION'] = '2024/2025'
app.config['CURRENT_TERM'] = 'First Term'
app.config['SESSION_START_DATE'] = ''
app.config['SESSION_END_DATE'] = ''
app.config['ENABLE_NOTIFICATIONS'] = True
app.config['ENABLE_SMS'] = False
app.config['ENABLE_EMAIL'] = True
app.config['CURRENCY'] = 'NGN'
app.config['CURRENCY_SYMBOL'] = '₦'

# Academic Settings (defaults)
app.config['DEFAULT_CLASS_CAPACITY'] = 40
app.config['ADMISSION_NUMBER_FORMAT'] = 'YEAR-SEQ'

# Grading System (defaults)
app.config['GRADE_A_MIN'] = 75.0
app.config['GRADE_B_MIN'] = 65.0
app.config['GRADE_C_MIN'] = 55.0
app.config['GRADE_D_MIN'] = 45.0
app.config['GRADE_A_LABEL'] = 'Excellent'
app.config['GRADE_B_LABEL'] = 'Very Good'
app.config['GRADE_C_LABEL'] = 'Good'
app.config['GRADE_D_LABEL'] = 'Credit'
app.config['GRADE_F_LABEL'] = 'Fail'

# Feature Toggles (defaults - all enabled)
app.config['ENABLE_ONLINE_ADMISSION'] = True
app.config['ENABLE_ONLINE_PAYMENT'] = True
app.config['ENABLE_ID_CARDS'] = True
app.config['ENABLE_REPORT_CARDS'] = True
app.config['ENABLE_ASSIGNMENTS'] = True
app.config['ENABLE_TESTS'] = True
app.config['ENABLE_EXAMS'] = True
app.config['ENABLE_ATTENDANCE'] = True
app.config['ENABLE_FEES'] = True
app.config['ENABLE_STORE'] = True
app.config['ENABLE_EXPENDITURES'] = True
app.config['ENABLE_SALARIES'] = True
app.config['ENABLE_SALARY_ADVANCES'] = True

# Access Control (defaults)
app.config['TEACHERS_CAN_ADD_LEARNERS'] = False
app.config['TEACHERS_CAN_ADD_STAFF'] = False
app.config['TEACHERS_CAN_CREATE_EXAMS'] = True
app.config['TEACHERS_CAN_VIEW_REPORTS'] = False
app.config['TEACHERS_CAN_MANAGE_FEES'] = False

# Display Settings (defaults)
app.config['ITEMS_PER_PAGE'] = 20
app.config['DATE_FORMAT'] = 'DD/MM/YYYY'
app.config['TIME_FORMAT'] = '24H'
app.config['NUMBER_FORMAT'] = 'COMMA'

# Fee Settings (defaults)
app.config['DEFAULT_FEE_TYPES'] = 'Tuition,PTA Levy,Library,Laboratory,Sports,Examination,Development Levy'
app.config['PAYMENT_METHODS'] = 'Cash,Bank Transfer,POS,Online Payment,Cheque'
app.config['RECEIPT_NUMBER_FORMAT'] = 'REC-YYYYMMDD-SEQ'

# Report Settings (defaults)
app.config['AUTO_INCLUDE_LOGO'] = True
app.config['REQUIRE_SIGNATURES'] = True
app.config['DEFAULT_REPORT_FORMAT'] = 'PDF'

# Notification Triggers (defaults)
app.config['NOTIFY_FEE_PAYMENT'] = True
app.config['NOTIFY_EXAM_RESULTS'] = True
app.config['NOTIFY_ATTENDANCE'] = False

# Security Settings (defaults)
app.config['MIN_PASSWORD_LENGTH'] = 6
app.config['REQUIRE_PASSWORD_COMPLEXITY'] = False
app.config['SESSION_TIMEOUT_MINUTES'] = 60
app.config['MAX_LOGIN_ATTEMPTS'] = 5

# System Settings (defaults)
app.config['AUTO_BACKUP_ENABLED'] = False
app.config['BACKUP_FREQUENCY'] = 'daily'
app.config['DATA_RETENTION_DAYS'] = 365

# Login Page Settings (defaults)
app.config['LOGIN_PAGE_TITLE'] = 'Wajina Suite - School Management System'
app.config['LOGIN_WELCOME_MESSAGE'] = 'Welcome Back'
app.config['LOGIN_SUBTITLE'] = 'School Management System'
app.config['LOGIN_SHOW_LOGO'] = True
app.config['LOGIN_USE_LOGO_AS_BACKGROUND'] = False
app.config['LOGIN_LOGO_BACKGROUND_OPACITY'] = 0.1
app.config['LOGIN_LOGO_BACKGROUND_SIZE'] = 'cover'  # cover, contain, auto
app.config['LOGIN_LOGO_BACKGROUND_POSITION'] = 'center'  # center, top, bottom, left, right
app.config['LOGIN_LOGO_BACKGROUND_REPEAT'] = 'no-repeat'  # no-repeat, repeat, repeat-x, repeat-y
app.config['LOGIN_BACKGROUND_IMAGE'] = ''
app.config['LOGIN_BACKGROUND_COLOR'] = '#f8f9fa'
app.config['LOGIN_SHOW_DEFAULT_CREDENTIALS'] = True

# Landing Page Settings (defaults)
app.config['LANDING_PAGE_TITLE'] = 'Wajina Suite - School Management System'
app.config['LANDING_HERO_TITLE'] = 'Wajina International School'
app.config['LANDING_HERO_SUBTITLE'] = 'Comprehensive School Management System'
app.config['LANDING_SHOW_LOGO'] = True
app.config['LANDING_SHOW_HERO_BUTTON'] = True
app.config['LANDING_HERO_BUTTON_TEXT'] = 'Apply for Admission Online'
app.config['LANDING_SHOW_FEATURES'] = True
app.config['LANDING_SHOW_PORTALS'] = True
app.config['LANDING_BACKGROUND_COLOR'] = '#9ACD32'
app.config['LANDING_BACKGROUND_IMAGE'] = ''

# Email Configuration (defaults - can be updated in settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = ''  # Set in settings
app.config['MAIL_PASSWORD'] = ''  # Set in settings
app.config['MAIL_DEFAULT_SENDER'] = ''  # Set in settings

# Flutterwave Payment Gateway Configuration
app.config['FLUTTERWAVE_PUBLIC_KEY'] = ''  # Set in settings or environment variable
app.config['FLUTTERWAVE_SECRET_KEY'] = ''  # Set in settings or environment variable
app.config['FLUTTERWAVE_ENCRYPTION_KEY'] = ''  # Set in settings or environment variable
app.config['FLUTTERWAVE_ENVIRONMENT'] = 'sandbox'  # sandbox or live

# Create upload folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'passports'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logo'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'login'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'receipts'), exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail(app)

# Import models (must be after db is created)
# Import routes (must be after models are imported)
# These imports are done at the end to avoid circular imports

# Import models and routes after db is created (to avoid circular imports)
from models import User, Learner, Staff, Class, Subject, Attendance, Fee, Exam, ExamResult, AcademicRecord, StoreItem, StoreTransaction, Expenditure, Assignment, AssignmentResult, Test, TestResult, AdmissionApplication, PaymentTransaction, Salary, SalaryAdvance, SchoolTimetable, ExamTimetable
from routes import *

# Setup login manager
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


# Context processor to make theme available in all templates
@app.context_processor
def inject_theme():
    return dict(current_theme=app.config.get('APP_THEME', 'lemon-green'))

# Initialize database on app startup (for production with gunicorn)
def initialize_database():
    """Initialize database tables and create default admin user"""
    try:
        # Check if tables exist by trying to query
        User.query.first()
        print("Database already initialized.")
    except Exception:
        # Tables don't exist, initialize database
        print("Initializing database...")
        db.create_all()
        
        # Try to add missing columns
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Add passport_photograph column if it doesn't exist
            try:
                columns = [col['name'] for col in inspector.get_columns('learners')]
                if 'passport_photograph' not in columns:
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE learners ADD COLUMN passport_photograph VARCHAR(255)'))
            except Exception:
                pass
            
            # Add receipt_file column if it doesn't exist
            try:
                exp_columns = [col['name'] for col in inspector.get_columns('expenditures')]
                if 'receipt_file' not in exp_columns:
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE expenditures ADD COLUMN receipt_file VARCHAR(255)'))
            except Exception:
                pass
            
            # Add password reset columns if they don't exist
            try:
                user_columns = [col['name'] for col in inspector.get_columns('users')]
                if 'reset_token' not in user_columns:
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)'))
                if 'reset_token_expiry' not in user_columns:
                    with db.engine.begin() as conn:
                        conn.execute(text('ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME'))
            except Exception:
                pass
        except Exception:
            pass
        
        # Create default admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@wajina.edu.ng',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
            print("Username: admin, Password: admin123")

# Initialize database when app starts (for production)
with app.app_context():
    initialize_database()

if __name__ == '__main__':
    with app.app_context():
        # Load settings from file if available
        from routes import load_settings_from_file
        load_settings_from_file()
        
        # Create all database tables
        db.create_all()
        
        # Add passport_photograph column if it doesn't exist
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('learners')]
            
            if 'passport_photograph' not in columns:
                print("Adding passport_photograph column to learners table...")
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE learners ADD COLUMN passport_photograph VARCHAR(255)'))
                print("Column added successfully!")
        except Exception as e:
            print(f"Note: Could not add column automatically: {str(e)}")
            print("You may need to delete the database and recreate it.")
        
        # Add receipt_file column to expenditures table if it doesn't exist
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            exp_columns = [col['name'] for col in inspector.get_columns('expenditures')]
            
            if 'receipt_file' not in exp_columns:
                print("Adding receipt_file column to expenditures table...")
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE expenditures ADD COLUMN receipt_file VARCHAR(255)'))
                print("Column added successfully!")
        except Exception as e:
            print(f"Note: Could not add receipt_file column automatically: {str(e)}")
        
        # Add password reset token columns to users table if they don't exist
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'reset_token' not in user_columns:
                print("Adding reset_token column to users table...")
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)'))
                print("reset_token column added successfully!")
            
            if 'reset_token_expiry' not in user_columns:
                print("Adding reset_token_expiry column to users table...")
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME'))
                print("reset_token_expiry column added successfully!")
        except Exception as e:
            print(f"Note: Could not add password reset columns automatically: {str(e)}")
        
        # Create default admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@wajina.edu.ng',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("Default admin user created!")
            print("Username: admin")
            print("Password: admin123")
            print("=" * 50)
    
    # Get port from environment variable (for production) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Only run in debug mode if not in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("\n" + "=" * 50)
    print("Wajina Suite - School Management System")
    print(f"Server starting on http://0.0.0.0:{port}")
    print("=" * 50 + "\n")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

