"""
Routes for Wajina Suite
"""

from app import app, login_manager, mail
from database import db
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from models import User, Learner, Staff, Class, Subject, Attendance, Fee, Exam, ExamResult, AcademicRecord, StoreItem, StoreTransaction, Expenditure, Assignment, AssignmentResult, Test, TestResult, AdmissionApplication, PaymentTransaction, Salary, SalaryAdvance, SchoolTimetable, ExamTimetable, EWallet, EWalletTransaction
from datetime import datetime, date, timedelta
from functools import wraps
from sqlalchemy import case
from sqlalchemy.orm import joinedload
from report_utils import (
    generate_learner_pdf, generate_attendance_pdf, generate_fee_pdf,
    generate_learner_csv, generate_attendance_csv, generate_fee_csv,
    generate_store_pdf, generate_expenditure_pdf, generate_store_csv, generate_expenditure_csv,
    generate_report_card_pdf, generate_report_card_csv
)
import os
from io import BytesIO
import csv
import json
import uuid
import qrcode
from PIL import Image, ImageDraw, ImageFont


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_settings_file_path():
    """Get path to settings JSON file"""
    return os.path.join('instance', 'settings.json')


def load_settings_from_file():
    """Load settings from JSON file"""
    settings_file = get_settings_file_path()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Update app config with loaded settings
                for key, value in settings.items():
                    # Ensure proper type conversion for settings
                    app.config[key] = value
        except Exception as e:
            print(f"Error loading settings from file: {e}")
            import traceback
            traceback.print_exc()
            pass


def save_settings_to_file():
    """Save current settings to JSON file"""
    settings_file = get_settings_file_path()
    os.makedirs('instance', exist_ok=True)
    
    settings_to_save = {
        # School Information
        'SCHOOL_NAME': app.config.get('SCHOOL_NAME', ''),
        'SCHOOL_ADDRESS': app.config.get('SCHOOL_ADDRESS', ''),
        'SCHOOL_PHONE': app.config.get('SCHOOL_PHONE', ''),
        'SCHOOL_EMAIL': app.config.get('SCHOOL_EMAIL', ''),
        'SCHOOL_WEBSITE': app.config.get('SCHOOL_WEBSITE', ''),
        'SCHOOL_LOGO': app.config.get('SCHOOL_LOGO', ''),
        
        # Academic Settings
        'CURRENT_SESSION': app.config.get('CURRENT_SESSION', ''),
        'CURRENT_TERM': app.config.get('CURRENT_TERM', ''),
        'SESSION_START_DATE': app.config.get('SESSION_START_DATE', ''),
        'SESSION_END_DATE': app.config.get('SESSION_END_DATE', ''),
        'DEFAULT_CLASS_CAPACITY': app.config.get('DEFAULT_CLASS_CAPACITY', 40),
        'ADMISSION_NUMBER_FORMAT': app.config.get('ADMISSION_NUMBER_FORMAT', 'YEAR-SEQ'),
        
        # Grading System
        'GRADE_A_MIN': app.config.get('GRADE_A_MIN', 75),
        'GRADE_B_MIN': app.config.get('GRADE_B_MIN', 65),
        'GRADE_C_MIN': app.config.get('GRADE_C_MIN', 55),
        'GRADE_D_MIN': app.config.get('GRADE_D_MIN', 45),
        'GRADE_A_LABEL': app.config.get('GRADE_A_LABEL', 'Excellent'),
        'GRADE_B_LABEL': app.config.get('GRADE_B_LABEL', 'Very Good'),
        'GRADE_C_LABEL': app.config.get('GRADE_C_LABEL', 'Good'),
        'GRADE_D_LABEL': app.config.get('GRADE_D_LABEL', 'Credit'),
        'GRADE_F_LABEL': app.config.get('GRADE_F_LABEL', 'Fail'),
        
        # Feature Toggles
        'ENABLE_ONLINE_ADMISSION': app.config.get('ENABLE_ONLINE_ADMISSION', True),
        'ENABLE_ONLINE_PAYMENT': app.config.get('ENABLE_ONLINE_PAYMENT', True),
        'ENABLE_ID_CARDS': app.config.get('ENABLE_ID_CARDS', True),
        'ENABLE_REPORT_CARDS': app.config.get('ENABLE_REPORT_CARDS', True),
        'ENABLE_ASSIGNMENTS': app.config.get('ENABLE_ASSIGNMENTS', True),
        'ENABLE_TESTS': app.config.get('ENABLE_TESTS', True),
        'ENABLE_EXAMS': app.config.get('ENABLE_EXAMS', True),
        'ENABLE_ATTENDANCE': app.config.get('ENABLE_ATTENDANCE', True),
        'ENABLE_FEES': app.config.get('ENABLE_FEES', True),
        'ENABLE_STORE': app.config.get('ENABLE_STORE', True),
        'ENABLE_EXPENDITURES': app.config.get('ENABLE_EXPENDITURES', True),
        'ENABLE_SALARIES': app.config.get('ENABLE_SALARIES', True),
        'ENABLE_SALARY_ADVANCES': app.config.get('ENABLE_SALARY_ADVANCES', True),
        
        # Access Control
        'TEACHERS_CAN_ADD_LEARNERS': app.config.get('TEACHERS_CAN_ADD_LEARNERS', False),
        'TEACHERS_CAN_ADD_STAFF': app.config.get('TEACHERS_CAN_ADD_STAFF', False),
        'TEACHERS_CAN_CREATE_EXAMS': app.config.get('TEACHERS_CAN_CREATE_EXAMS', True),
        'TEACHERS_CAN_VIEW_REPORTS': app.config.get('TEACHERS_CAN_VIEW_REPORTS', False),
        'TEACHERS_CAN_MANAGE_FEES': app.config.get('TEACHERS_CAN_MANAGE_FEES', False),
        
        # Display Settings
        'ITEMS_PER_PAGE': app.config.get('ITEMS_PER_PAGE', 20),
        'DATE_FORMAT': app.config.get('DATE_FORMAT', 'DD/MM/YYYY'),
        'TIME_FORMAT': app.config.get('TIME_FORMAT', '24H'),
        'NUMBER_FORMAT': app.config.get('NUMBER_FORMAT', 'COMMA'),
        
        # Fee Settings
        'DEFAULT_FEE_TYPES': app.config.get('DEFAULT_FEE_TYPES', 'Tuition,PTA Levy,Library,Laboratory,Sports,Examination,Development Levy'),
        'PAYMENT_METHODS': app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque'),
        'RECEIPT_NUMBER_FORMAT': app.config.get('RECEIPT_NUMBER_FORMAT', 'REC-YYYYMMDD-SEQ'),
        
        # Report Settings
        'AUTO_INCLUDE_LOGO': app.config.get('AUTO_INCLUDE_LOGO', True),
        'REQUIRE_SIGNATURES': app.config.get('REQUIRE_SIGNATURES', True),
        'DEFAULT_REPORT_FORMAT': app.config.get('DEFAULT_REPORT_FORMAT', 'PDF'),
        
        # Notification Settings
        'ENABLE_NOTIFICATIONS': app.config.get('ENABLE_NOTIFICATIONS', True),
        'ENABLE_SMS': app.config.get('ENABLE_SMS', False),
        'ENABLE_EMAIL': app.config.get('ENABLE_EMAIL', True),
        'NOTIFY_FEE_PAYMENT': app.config.get('NOTIFY_FEE_PAYMENT', True),
        'NOTIFY_EXAM_RESULTS': app.config.get('NOTIFY_EXAM_RESULTS', True),
        'NOTIFY_ATTENDANCE': app.config.get('NOTIFY_ATTENDANCE', False),
        
        # Email Configuration
        'MAIL_SERVER': app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': app.config.get('MAIL_PORT', 587),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME', ''),
        'MAIL_PASSWORD': app.config.get('MAIL_PASSWORD', ''),
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER', ''),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS', True),
        'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL', False),
        
        # Currency Settings
        'CURRENCY': app.config.get('CURRENCY', 'NGN'),
        'CURRENCY_SYMBOL': app.config.get('CURRENCY_SYMBOL', '₦'),
        
        # Flutterwave Payment Gateway Settings
        'FLUTTERWAVE_PUBLIC_KEY': app.config.get('FLUTTERWAVE_PUBLIC_KEY', ''),
        'FLUTTERWAVE_SECRET_KEY': app.config.get('FLUTTERWAVE_SECRET_KEY', ''),
        'FLUTTERWAVE_ENCRYPTION_KEY': app.config.get('FLUTTERWAVE_ENCRYPTION_KEY', ''),
        'FLUTTERWAVE_ENVIRONMENT': app.config.get('FLUTTERWAVE_ENVIRONMENT', 'sandbox'),
        
        # Theme Settings
        'APP_THEME': app.config.get('APP_THEME', 'lemon-green'),
        
        # Security Settings
        'MIN_PASSWORD_LENGTH': app.config.get('MIN_PASSWORD_LENGTH', 6),
        'REQUIRE_PASSWORD_COMPLEXITY': app.config.get('REQUIRE_PASSWORD_COMPLEXITY', False),
        'SESSION_TIMEOUT_MINUTES': app.config.get('SESSION_TIMEOUT_MINUTES', 60),
        'MAX_LOGIN_ATTEMPTS': app.config.get('MAX_LOGIN_ATTEMPTS', 5),
        
        # System Settings
        'AUTO_BACKUP_ENABLED': app.config.get('AUTO_BACKUP_ENABLED', False),
        'BACKUP_FREQUENCY': app.config.get('BACKUP_FREQUENCY', 'daily'),
        'DATA_RETENTION_DAYS': app.config.get('DATA_RETENTION_DAYS', 365),
        
        # Login Page Settings
        'LOGIN_PAGE_TITLE': app.config.get('LOGIN_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'LOGIN_WELCOME_MESSAGE': app.config.get('LOGIN_WELCOME_MESSAGE', 'Welcome Back'),
        'LOGIN_SUBTITLE': app.config.get('LOGIN_SUBTITLE', 'School Management System'),
        'LOGIN_SHOW_LOGO': app.config.get('LOGIN_SHOW_LOGO', True),
        'LOGIN_USE_LOGO_AS_BACKGROUND': app.config.get('LOGIN_USE_LOGO_AS_BACKGROUND', False),
        'LOGIN_LOGO_BACKGROUND_OPACITY': app.config.get('LOGIN_LOGO_BACKGROUND_OPACITY', 0.1),
        'LOGIN_LOGO_BACKGROUND_SIZE': app.config.get('LOGIN_LOGO_BACKGROUND_SIZE', 'cover'),
        'LOGIN_LOGO_BACKGROUND_POSITION': app.config.get('LOGIN_LOGO_BACKGROUND_POSITION', 'center'),
        'LOGIN_LOGO_BACKGROUND_REPEAT': app.config.get('LOGIN_LOGO_BACKGROUND_REPEAT', 'no-repeat'),
        'LOGIN_BACKGROUND_IMAGE': app.config.get('LOGIN_BACKGROUND_IMAGE', ''),
        'LOGIN_BACKGROUND_COLOR': app.config.get('LOGIN_BACKGROUND_COLOR', '#f8f9fa'),
        'LOGIN_SHOW_DEFAULT_CREDENTIALS': app.config.get('LOGIN_SHOW_DEFAULT_CREDENTIALS', True),
        
        # Landing Page Settings
        'LANDING_PAGE_TITLE': app.config.get('LANDING_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'LANDING_HERO_TITLE': app.config.get('LANDING_HERO_TITLE', 'Wajina International School'),
        'LANDING_HERO_SUBTITLE': app.config.get('LANDING_HERO_SUBTITLE', 'Comprehensive School Management System'),
        'LANDING_SHOW_LOGO': app.config.get('LANDING_SHOW_LOGO', True),
        'LANDING_SHOW_HERO_BUTTON': app.config.get('LANDING_SHOW_HERO_BUTTON', True),
        'LANDING_HERO_BUTTON_TEXT': app.config.get('LANDING_HERO_BUTTON_TEXT', 'Apply for Admission Online'),
        'LANDING_SHOW_FEATURES': app.config.get('LANDING_SHOW_FEATURES', True),
        'LANDING_SHOW_PORTALS': app.config.get('LANDING_SHOW_PORTALS', True),
        'LANDING_BACKGROUND_COLOR': app.config.get('LANDING_BACKGROUND_COLOR', '#9ACD32'),
        'LANDING_BACKGROUND_IMAGE': app.config.get('LANDING_BACKGROUND_IMAGE', ''),
        
        # ID Card Settings
        'ID_CARD_WIDTH': app.config.get('ID_CARD_WIDTH', 500),
        'ID_CARD_HEIGHT': app.config.get('ID_CARD_HEIGHT', 0),
        'ID_CARD_BORDER_RADIUS': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'ID_CARD_BG_COLOR': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'ID_CARD_HEADER_BG_COLOR': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'ID_CARD_FOOTER_BG_COLOR': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'ID_CARD_BORDER_COLOR': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'ID_CARD_BORDER_WIDTH': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'ID_CARD_LOGO_POSITION': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'ID_CARD_LOGO_HEIGHT': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'ID_CARD_LOGO_MARGIN_BOTTOM': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'ID_CARD_PHOTO_POSITION': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'ID_CARD_PHOTO_WIDTH': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'ID_CARD_PHOTO_HEIGHT': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'ID_CARD_PHOTO_BORDER_COLOR': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'ID_CARD_PHOTO_BORDER_WIDTH': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'ID_CARD_TEXT_POSITION': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'ID_CARD_NAME_FONT_SIZE': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'ID_CARD_LABEL_FONT_SIZE': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'ID_CARD_VALUE_FONT_SIZE': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'ID_CARD_TEXT_COLOR': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'ID_CARD_LABEL_COLOR': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'ID_CARD_QR_POSITION': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'ID_CARD_QR_SIZE': app.config.get('ID_CARD_QR_SIZE', 120),
        'ID_CARD_SHOW_QR': app.config.get('ID_CARD_SHOW_QR', True),
        'ID_CARD_HEADER_TITLE_SIZE': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'ID_CARD_HEADER_SUBTITLE_SIZE': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'ID_CARD_HEADER_TEXT_COLOR': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'ID_CARD_FOOTER_TEXT_COLOR': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'ID_CARD_FOOTER_FONT_SIZE': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
        print(f"Settings saved successfully to {settings_file}")
    except Exception as e:
        print(f"Error saving settings: {e}")
        import traceback
        traceback.print_exc()


def get_school_settings():
    """Helper function to get school settings for templates"""
    return {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_address': app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
        'school_phone': app.config.get('SCHOOL_PHONE', ''),
        'school_email': app.config.get('SCHOOL_EMAIL', ''),
        'school_website': app.config.get('SCHOOL_WEBSITE', ''),
        'school_logo': app.config.get('SCHOOL_LOGO', '')
    }




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        # Try to find user by username, email, or phone number
        user = None
        if username:
            # Try username first
            user = User.query.filter_by(username=username).first()
            # If not found, try email
            if not user:
                user = User.query.filter_by(email=username).first()
            # If still not found, try phone number
            if not user:
                user = User.query.filter_by(phone=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # Redirect to appropriate portal based on role
            if user.role == 'parent':
                return redirect(url_for('parent_portal'))
            elif user.role == 'learner':
                return redirect(url_for('learner_portal'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_portal'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    # Get login page settings - always reload from file to get latest
    load_settings_from_file()
    
    # Get all login settings with proper defaults and type conversion
    login_settings = {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_logo': app.config.get('SCHOOL_LOGO', ''),
        'login_page_title': app.config.get('LOGIN_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'login_welcome_message': app.config.get('LOGIN_WELCOME_MESSAGE', 'Welcome Back'),
        'login_subtitle': app.config.get('LOGIN_SUBTITLE', 'School Management System'),
        'login_show_logo': bool(app.config.get('LOGIN_SHOW_LOGO', True)),
        'login_use_logo_as_background': bool(app.config.get('LOGIN_USE_LOGO_AS_BACKGROUND', False)),
        'login_logo_background_opacity': float(app.config.get('LOGIN_LOGO_BACKGROUND_OPACITY', 0.1)),
        'login_logo_background_size': app.config.get('LOGIN_LOGO_BACKGROUND_SIZE', 'cover'),
        'login_logo_background_position': app.config.get('LOGIN_LOGO_BACKGROUND_POSITION', 'center'),
        'login_logo_background_repeat': app.config.get('LOGIN_LOGO_BACKGROUND_REPEAT', 'no-repeat'),
        'login_background_image': app.config.get('LOGIN_BACKGROUND_IMAGE', ''),
        'login_background_color': app.config.get('LOGIN_BACKGROUND_COLOR', '#f8f9fa'),
        'login_show_default_credentials': bool(app.config.get('LOGIN_SHOW_DEFAULT_CREDENTIALS', True)),
    }
    
    return render_template('auth/login.html', settings=login_settings)


@app.route('/')
def home():
    """Home/Landing page with portal access"""
    if current_user.is_authenticated:
        # If logged in, redirect to their dashboard
        return redirect(url_for('dashboard'))
    
    # Get landing page settings
    load_settings_from_file()
    landing_settings = {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_address': app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
        'school_phone': app.config.get('SCHOOL_PHONE', ''),
        'school_email': app.config.get('SCHOOL_EMAIL', ''),
        'school_website': app.config.get('SCHOOL_WEBSITE', ''),
        'school_logo': app.config.get('SCHOOL_LOGO', ''),
        'landing_page_title': app.config.get('LANDING_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'landing_hero_title': app.config.get('LANDING_HERO_TITLE', 'Wajina International School'),
        'landing_hero_subtitle': app.config.get('LANDING_HERO_SUBTITLE', 'Comprehensive School Management System'),
        'landing_show_logo': bool(app.config.get('LANDING_SHOW_LOGO', True)),
        'landing_show_hero_button': bool(app.config.get('LANDING_SHOW_HERO_BUTTON', True)),
        'landing_hero_button_text': app.config.get('LANDING_HERO_BUTTON_TEXT', 'Apply for Admission Online'),
        'landing_show_features': bool(app.config.get('LANDING_SHOW_FEATURES', True)),
        'landing_show_portals': bool(app.config.get('LANDING_SHOW_PORTALS', True)),
        'landing_background_color': app.config.get('LANDING_BACKGROUND_COLOR', '#9ACD32'),
        'landing_background_image': app.config.get('LANDING_BACKGROUND_IMAGE', ''),
    }
    
    return render_template('home.html', settings=landing_settings)


@app.route('/terms-and-conditions')
def terms_and_conditions():
    """Terms and Conditions page"""
    load_settings_from_file()
    settings = {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_address': app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
        'school_phone': app.config.get('SCHOOL_PHONE', ''),
        'school_email': app.config.get('SCHOOL_EMAIL', ''),
    }
    return render_template('public/terms_and_conditions.html', settings=settings)


@app.route('/offline')
def offline():
    """Offline page when no internet connection"""
    return render_template('offline.html')


@app.route('/manifest.json')
def manifest():
    """Serve web app manifest"""
    from flask import send_from_directory
    return send_from_directory('static', 'manifest.json', mimetype='application/json')


@app.route('/service-worker.js')
def service_worker():
    """Serve service worker"""
    from flask import send_from_directory
    return send_from_directory('static/js', 'service-worker.js', mimetype='application/javascript')


@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy and Data Protection page"""
    load_settings_from_file()
    settings = {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_address': app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
        'school_phone': app.config.get('SCHOOL_PHONE', ''),
        'school_email': app.config.get('SCHOOL_EMAIL', ''),
    }
    return render_template('public/privacy_policy.html', settings=settings)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Get login page settings
    load_settings_from_file()
    login_settings = {
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_logo': app.config.get('SCHOOL_LOGO', ''),
        'login_show_logo': bool(app.config.get('LOGIN_SHOW_LOGO', True)),
        'login_use_logo_as_background': bool(app.config.get('LOGIN_USE_LOGO_AS_BACKGROUND', False)),
        'login_logo_background_opacity': float(app.config.get('LOGIN_LOGO_BACKGROUND_OPACITY', 0.1)),
        'login_logo_background_size': app.config.get('LOGIN_LOGO_BACKGROUND_SIZE', 'cover'),
        'login_logo_background_position': app.config.get('LOGIN_LOGO_BACKGROUND_POSITION', 'center'),
        'login_logo_background_repeat': app.config.get('LOGIN_LOGO_BACKGROUND_REPEAT', 'no-repeat'),
        'login_background_image': app.config.get('LOGIN_BACKGROUND_IMAGE', ''),
        'login_background_color': app.config.get('LOGIN_BACKGROUND_COLOR', '#f8f9fa'),
    }
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        
        if not email and not username:
            flash('Please provide either your email address, username, or phone number.', 'danger')
            return render_template('auth/forgot_password.html', settings=login_settings)
        
        # Find user by email, username, or phone number
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        elif username:
            # Try username first
            user = User.query.filter_by(username=username).first()
            # If not found, try phone number
            if not user:
                user = User.query.filter_by(phone=username).first()
        
        if user and user.is_active:
            # Check if email is configured
            if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
                flash('Password reset emails are not configured. Please contact the administrator.', 'danger')
                return render_template('auth/forgot_password.html', settings=login_settings)
            
            # Generate reset token
            reset_token = str(uuid.uuid4())
            user.reset_token = reset_token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
            db.session.commit()
            
            # Send reset email
            try:
                reset_url = url_for('reset_password', token=reset_token, _external=True)
                school_name = app.config.get('SCHOOL_NAME', 'Wajina International School')
                
                msg = Message(
                    subject=f'Password Reset Request - {school_name}',
                    recipients=[user.email],
                    sender=app.config.get('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME', 'noreply@wajina.com'))
                )
                
                msg.body = f"""
Hello {user.first_name} {user.last_name},

You have requested to reset your password for your {school_name} account.

To reset your password, please click on the following link:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
{school_name} Administration
"""
                
                mail.send(msg)
                flash('Password reset instructions have been sent to your email address. Please check your inbox.', 'success')
            except Exception as e:
                print(f"Error sending password reset email: {str(e)}")
                import traceback
                traceback.print_exc()
                flash('Failed to send password reset email. Please contact the administrator.', 'danger')
                # Clear the token if email failed
                user.reset_token = None
                user.reset_token_expiry = None
                db.session.commit()
        else:
            # Don't reveal if user exists or not (security best practice)
            flash('If an account exists with that email, username, or phone number, password reset instructions have been sent.', 'info')
        
        return render_template('auth/forgot_password.html', settings=login_settings)
    
    return render_template('auth/forgot_password.html', settings=login_settings)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Find user by token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        flash('Invalid or expired reset token. Please request a new password reset.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Check if token has expired
    if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
        flash('This password reset link has expired. Please request a new one.', 'danger')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate passwords
        min_length = app.config.get('MIN_PASSWORD_LENGTH', 6)
        if not new_password:
            flash('Please enter a new password.', 'danger')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        if len(new_password) < min_length:
            flash(f'Password must be at least {min_length} characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        # Update password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', token=token, user=user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with statistics based on user role - redirects to portals"""
    # Redirect to appropriate portal
    if current_user.role == 'parent':
        return redirect(url_for('parent_portal'))
    elif current_user.role == 'learner':
        return redirect(url_for('learner_portal'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_portal'))
    elif current_user.role == 'cashier':
        return redirect(url_for('cashier_portal'))
    
    # Admin and other roles use the main dashboard
    stats = {}
    
    try:
        if current_user.role == 'admin':
            stats['total_learners'] = Learner.query.filter_by(status='active').count()
            stats['total_staff'] = Staff.query.filter_by(status='active').count()
            stats['total_classes'] = Class.query.filter_by(status='active').count()
            stats['pending_fees'] = Fee.query.filter_by(status='pending').count()
            stats['total_fees_amount'] = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
            stats['recent_admissions'] = Learner.query.order_by(Learner.created_at.desc()).limit(5).all()
            
            # Parent/Guardian statistics
            # Get unique parents (by parent_name and parent_phone combination)
            parents_data = db.session.query(
                Learner.parent_name,
                Learner.parent_phone,
                Learner.parent_email,
                Learner.parent_address,
                db.func.count(Learner.id).label('children_count')
            ).filter(
                Learner.status == 'active',
                Learner.parent_name.isnot(None),
                Learner.parent_name != ''
            ).group_by(
                Learner.parent_name,
                Learner.parent_phone,
                Learner.parent_email,
                Learner.parent_address
            ).all()
            
            stats['total_parents'] = len(parents_data)
            stats['parents_with_multiple_children'] = len([p for p in parents_data if p.children_count > 1])
            stats['parents_data'] = parents_data[:10]  # Top 10 for dashboard preview
            
            # Salary/Wage Bill Statistics
            current_month = datetime.now().strftime('%B %Y')
            current_year = datetime.now().year
            
            # Total monthly wage bill (sum of all active staff basic salaries)
            total_monthly_wage_bill = db.session.query(db.func.sum(Staff.salary)).filter(
                Staff.status == 'active',
                Staff.salary.isnot(None)
            ).scalar() or 0
            
            # This month's paid salaries
            this_month_paid = db.session.query(db.func.sum(Salary.net_salary)).filter(
                Salary.month == datetime.now().strftime('%B'),
                Salary.year == current_year,
                Salary.status == 'paid'
            ).scalar() or 0
            
            # Pending salaries for this month
            this_month_pending = db.session.query(db.func.sum(Salary.net_salary)).filter(
                Salary.month == datetime.now().strftime('%B'),
                Salary.year == current_year,
                Salary.status == 'pending'
            ).scalar() or 0
            
            # Salary advance statistics
            pending_advances = SalaryAdvance.query.filter_by(status='pending').count()
            approved_advances = SalaryAdvance.query.filter_by(status='approved').count()
            total_advance_amount = db.session.query(db.func.sum(SalaryAdvance.amount)).filter(
                SalaryAdvance.status.in_(['pending', 'approved', 'paid'])
            ).scalar() or 0
            
            stats['total_monthly_wage_bill'] = float(total_monthly_wage_bill)
            stats['this_month_paid'] = float(this_month_paid)
            stats['this_month_pending'] = float(this_month_pending)
            stats['pending_advances'] = pending_advances
            stats['approved_advances'] = approved_advances
            stats['total_advance_amount'] = float(total_advance_amount)
            
            # E-Wallet Statistics
            total_wallet_balance = db.session.query(db.func.sum(EWallet.balance)).scalar() or 0
            total_wallets = EWallet.query.count()
            active_wallets = EWallet.query.filter_by(status='active').count()
            
            # Total deposits (all time)
            total_deposits = db.session.query(db.func.sum(EWalletTransaction.amount)).filter(
                EWalletTransaction.transaction_type == 'deposit',
                EWalletTransaction.status == 'completed'
            ).scalar() or 0
            
            # Total deposits this month
            month_start = date.today().replace(day=1)
            deposits_this_month = db.session.query(db.func.sum(EWalletTransaction.amount)).filter(
                EWalletTransaction.transaction_type == 'deposit',
                EWalletTransaction.status == 'completed',
                EWalletTransaction.created_at >= month_start
            ).scalar() or 0
            
            # Total withdrawals
            total_withdrawals = db.session.query(db.func.sum(EWalletTransaction.amount)).filter(
                EWalletTransaction.transaction_type == 'withdrawal',
                EWalletTransaction.status == 'completed'
            ).scalar() or 0
            
            # Total payments from wallets
            total_wallet_payments = db.session.query(db.func.sum(EWalletTransaction.amount)).filter(
                EWalletTransaction.transaction_type == 'payment',
                EWalletTransaction.status == 'completed'
            ).scalar() or 0
            
            stats['total_wallet_balance'] = float(total_wallet_balance)
            stats['total_wallets'] = total_wallets
            stats['active_wallets'] = active_wallets
            stats['total_deposits'] = float(total_deposits)
            stats['deposits_this_month'] = float(deposits_this_month)
            stats['total_withdrawals'] = float(total_withdrawals)
            stats['total_wallet_payments'] = float(total_wallet_payments)
        elif current_user.role == 'teacher':
            staff = Staff.query.filter_by(user_id=current_user.id).first()
            if staff:
                stats['my_classes'] = Class.query.filter_by(class_teacher_id=staff.id).count()
                stats['my_subjects'] = Subject.query.filter_by(teacher_id=staff.id).count()
            else:
                stats['my_classes'] = 0
                stats['my_subjects'] = 0
        elif current_user.role == 'learner':
            learner = Learner.query.filter_by(user_id=current_user.id).first()
            if learner:
                stats['my_attendance'] = Attendance.query.filter_by(learner_id=learner.id).count()
                stats['pending_fees'] = Fee.query.filter_by(learner_id=learner.id, status='pending').count()
                stats['my_results'] = ExamResult.query.filter_by(learner_id=learner.id).count()
            else:
                stats['my_attendance'] = 0
                stats['pending_fees'] = 0
                stats['my_results'] = 0
    except Exception as e:
        import traceback
        print(f"Dashboard error: {str(e)}")
        print(traceback.format_exc())
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        stats = {}
    
    return render_template('dashboard.html', stats=stats)


# Learner Routes
@app.route('/learners')
@login_required
@role_required('admin')
def learners():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    
    query = Learner.query.join(User).filter(User.is_active == True)
    
    if search:
        query = query.filter(
            db.or_(
                Learner.admission_number.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    if class_filter:
        query = query.filter(Learner.current_class == class_filter)
    
    learners = query.order_by(Learner.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    classes = Class.query.filter_by(status='active').all()
    
    return render_template('learners/list.html', learners=learners, classes=classes, search=search, class_filter=class_filter)


@app.route('/learners/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_learner():
    if request.method == 'POST':
        try:
            # Auto-generate admission number
            year = datetime.now().strftime('%Y')
            # Format: ADM + Year + Sequential number (e.g., ADM2024001)
            prefix = 'ADM' + year
            
            # Find the next sequential number for this year
            search_pattern = prefix + '%'
            existing_learners = Learner.query.filter(Learner.admission_number.like(search_pattern)).all()
            max_num = 0
            for learner in existing_learners:
                try:
                    # Extract number from admission number (e.g., "ADM2024001" -> 1)
                    num_str = learner.admission_number.replace(prefix, '')
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_num:
                            max_num = num
                except:
                    pass
            
            admission_number = prefix + str(max_num + 1).zfill(3)
            
            # Handle passport photograph upload
            passport_photo_path = None
            if 'passport_photograph' in request.files:
                file = request.files['passport_photograph']
                if file and file.filename:
                    # Validate file type
                    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('Invalid file type. Please upload JPG, PNG, or GIF image.', 'danger')
                        classes = Class.query.filter_by(status='active').all()
                        return render_template('learners/add.html', classes=classes, current_date=date.today())
                    
                    # Generate unique filename using the auto-generated admission number
                    filename = f"passport_{admission_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'passports', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    # Save file
                    file.save(filepath)
                    passport_photo_path = f"passports/{filename}"
            
            # Create user account
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                phone=request.form.get('phone'),
                role='learner'
            )
            user.set_password(request.form.get('password') or 'learner123')
            
            db.session.add(user)
            db.session.flush()
            
            # Create learner profile
            learner = Learner(
                user_id=user.id,
                admission_number=admission_number,
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                address=request.form.get('address'),
                state_of_origin=request.form.get('state_of_origin'),
                lga=request.form.get('lga'),
                blood_group=request.form.get('blood_group'),
                parent_name=request.form.get('parent_name'),
                parent_phone=request.form.get('parent_phone'),
                parent_email=request.form.get('parent_email'),
                parent_address=request.form.get('parent_address'),
                emergency_contact=request.form.get('emergency_contact'),
                current_class=request.form.get('current_class'),
                current_session=request.form.get('current_session'),
                passport_photograph=passport_photo_path,
                admission_date=datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d').date() if request.form.get('admission_date') else date.today()
            )
            
            db.session.add(learner)
            db.session.commit()
            
            flash('Learner added successfully!', 'success')
            return redirect(url_for('learners'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding learner: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    return render_template('learners/add.html', classes=classes, current_date=date.today())


@app.route('/learners/<int:id>')
@login_required
def view_learner(id):
    learner = Learner.query.get_or_404(id)
    if current_user.role == 'learner' and learner.user_id != current_user.id:
        flash('You can only view your own profile.', 'danger')
        return redirect(url_for('dashboard'))
    
    attendances = Attendance.query.filter_by(learner_id=learner.id).order_by(Attendance.date.desc()).limit(10).all()
    fees = Fee.query.filter_by(learner_id=learner.id).order_by(Fee.due_date.desc()).limit(10).all()
    results = ExamResult.query.filter_by(learner_id=learner.id).order_by(ExamResult.created_at.desc()).limit(10).all()
    
    return render_template('learners/view.html', learner=learner, attendances=attendances, fees=fees, results=results)


# Staff Routes
@app.route('/staff')
@login_required
@role_required('admin')
def staff():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Staff.query.join(User).filter(User.is_active == True)
    
    if search:
        query = query.filter(
            db.or_(
                Staff.staff_id.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    staff_list = query.order_by(Staff.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('staff/list.html', staff_list=staff_list, search=search)


@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_staff():
    if request.method == 'POST':
        try:
            # Handle passport photograph upload
            passport_photo_path = None
            if 'passport_photograph' in request.files:
                file = request.files['passport_photograph']
                if file and file.filename:
                    # Validate file type
                    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('Invalid file type. Please upload JPG, PNG, or GIF image.', 'danger')
                        return render_template('staff/add.html', current_date=date.today())
                    
                    # Generate unique filename
                    first_name_clean = request.form.get('first_name', 'staff').replace(' ', '_').replace('/', '_')
                    last_name_clean = request.form.get('last_name', 'member').replace(' ', '_').replace('/', '_')
                    filename = f"staff_{first_name_clean}_{last_name_clean}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    # Save file
                    file.save(filepath)
                    passport_photo_path = f"profiles/{filename}"
            
            # Auto-generate staff ID
            first_name = request.form.get('first_name', '').upper()
            last_name = request.form.get('last_name', '').upper()
            
            # Generate staff ID: First 3 letters of last name + First 2 letters of first name + Year + Sequential number
            year = datetime.now().strftime('%Y')
            prefix = (last_name[:3] if len(last_name) >= 3 else last_name.ljust(3, 'X')) + \
                     (first_name[:2] if len(first_name) >= 2 else first_name.ljust(2, 'X'))
            
            # Find the next sequential number for this prefix and year
            search_pattern = prefix + year + '%'
            existing_staff = Staff.query.filter(Staff.staff_id.like(search_pattern)).all()
            max_num = 0
            for s in existing_staff:
                try:
                    num = int(s.staff_id[-3:])  # Last 3 digits
                    if num > max_num:
                        max_num = num
                except:
                    pass
            
            staff_id = f"{prefix}{year}{str(max_num + 1).zfill(3)}"
            
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                phone=request.form.get('phone'),
                role=request.form.get('role', 'teacher'),
                profile_picture=passport_photo_path
            )
            user.set_password(request.form.get('password') or 'staff123')
            
            db.session.add(user)
            db.session.flush()
            
            staff = Staff(
                user_id=user.id,
                staff_id=staff_id,
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                address=request.form.get('address'),
                state_of_origin=request.form.get('state_of_origin'),
                lga=request.form.get('lga'),
                phone=request.form.get('phone'),
                qualification=request.form.get('qualification'),
                specialization=request.form.get('specialization'),
                employment_date=datetime.strptime(request.form.get('employment_date'), '%Y-%m-%d').date() if request.form.get('employment_date') else date.today(),
                employment_type=request.form.get('employment_type'),
                department=request.form.get('department'),
                designation=request.form.get('designation'),
                salary=float(request.form.get('salary', 0)) if request.form.get('salary') else None
            )
            
            db.session.add(staff)
            db.session.commit()
            
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('staff'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding staff: {str(e)}', 'danger')
    
    # Generate a preview staff ID for display
    preview_staff_id = "STAFF2024001"  # Default preview
    return render_template('staff/add.html', current_date=date.today(), preview_staff_id=preview_staff_id)


# Attendance Routes
@app.route('/attendance')
@login_required
@role_required('admin', 'teacher')
def attendance():
    date_filter = request.args.get('date', date.today().isoformat())
    class_filter = request.args.get('class', '')
    
    try:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except:
        filter_date = date.today()
    
    if class_filter:
        learners = Learner.query.filter_by(current_class=class_filter, status='active').all()
    else:
        learners = Learner.query.filter_by(status='active').all()
    
    # Get existing attendance for the date
    attendance_records = {}
    for learner in learners:
        att = Attendance.query.filter_by(learner_id=learner.id, date=filter_date).first()
        attendance_records[learner.id] = att
    
    classes = Class.query.filter_by(status='active').all()
    
    return render_template('attendance/mark.html', learners=learners, classes=classes, 
                          date_filter=filter_date, class_filter=class_filter, attendance_records=attendance_records)


@app.route('/attendance/mark', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def mark_attendance():
    data = request.get_json()
    date_str = data.get('date')
    attendances = data.get('attendances', [])
    
    try:
        att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        for att_data in attendances:
            learner_id = att_data.get('learner_id')
            status = att_data.get('status')
            remarks = att_data.get('remarks', '')
            
            # Check if attendance already exists
            existing = Attendance.query.filter_by(learner_id=learner_id, date=att_date).first()
            
            if existing:
                existing.status = status
                existing.remarks = remarks
                existing.marked_by = current_user.id
            else:
                new_attendance = Attendance(
                    learner_id=learner_id,
                    date=att_date,
                    status=status,
                    remarks=remarks,
                    marked_by=current_user.id
                )
                db.session.add(new_attendance)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Attendance marked successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


# Fee Routes
@app.route('/fees')
@login_required
@role_required('admin', 'accountant', 'cashier')
def fees():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Fee.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    fees = query.order_by(Fee.due_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('fees/list.html', fees=fees, status_filter=status_filter)


@app.route('/fees/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'accountant', 'cashier')
def add_fee():
    if request.method == 'POST':
        try:
            fee = Fee(
                learner_id=int(request.form.get('learner_id')),
                fee_type=request.form.get('fee_type'),
                amount=float(request.form.get('amount')),
                due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
                session=request.form.get('session'),
                term=request.form.get('term'),
                remarks=request.form.get('remarks')
            )
            
            db.session.add(fee)
            db.session.commit()
            
            flash('Fee added successfully!', 'success')
            return redirect(url_for('fees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding fee: {str(e)}', 'danger')
    
    learners = Learner.query.filter_by(status='active').all()
    return render_template('fees/add.html', learners=learners)


@app.route('/fees/<int:id>/pay', methods=['POST'])
@login_required
@role_required('admin', 'accountant', 'cashier')
def pay_fee(id):
    fee = Fee.query.get_or_404(id)
    
    try:
        fee.paid_date = date.today()
        fee.payment_method = request.form.get('payment_method')
        fee.receipt_number = request.form.get('receipt_number')
        fee.status = 'paid'
        
        db.session.commit()
        flash('Fee payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'danger')
    
    return redirect(url_for('fees'))


# Exam Routes
@app.route('/exams')
@login_required
@role_required('admin', 'teacher')
def exams():
    exams = Exam.query.order_by(Exam.exam_date.desc()).all()
    return render_template('exams/list.html', exams=exams)


@app.route('/exams/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_exam():
    if request.method == 'POST':
        try:
            exam = Exam(
                name=request.form.get('name'),
                exam_type=request.form.get('exam_type'),
                class_id=int(request.form.get('class_id')) if request.form.get('class_id') else None,
                subject_id=int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
                exam_date=datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date() if request.form.get('exam_date') else None,
                max_score=int(request.form.get('max_score', 100)),
                session=request.form.get('session'),
                term=request.form.get('term')
            )
            
            db.session.add(exam)
            db.session.commit()
            
            flash('Exam added successfully!', 'success')
            return redirect(url_for('exams'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding exam: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    return render_template('exams/add.html', classes=classes, subjects=subjects)


@app.route('/exams/<int:id>/results', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def exam_results(id):
    exam = Exam.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            results_data = request.get_json().get('results', [])
            
            for result_data in results_data:
                learner_id = result_data.get('learner_id')
                score = float(result_data.get('score'))
                
                # Calculate grade based on Nigerian grading system
                percentage = (score / exam.max_score) * 100
                if percentage >= 75:
                    grade = 'A'
                    remark = 'Excellent'
                elif percentage >= 65:
                    grade = 'B'
                    remark = 'Very Good'
                elif percentage >= 55:
                    grade = 'C'
                    remark = 'Good'
                elif percentage >= 45:
                    grade = 'D'
                    remark = 'Credit'
                else:
                    grade = 'F'
                    remark = 'Fail'
                
                # Check if result exists
                existing = ExamResult.query.filter_by(exam_id=exam.id, learner_id=learner_id).first()
                
                if existing:
                    existing.score = score
                    existing.grade = grade
                    existing.remark = remark
                else:
                    result = ExamResult(
                        exam_id=exam.id,
                        learner_id=learner_id,
                        score=score,
                        grade=grade,
                        remark=remark
                    )
                    db.session.add(result)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Results saved successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # Get learners for the exam
    if exam.class_id and exam.class_ref:
        learners = Learner.query.filter_by(current_class=exam.class_ref.name, status='active').all()
    else:
        learners = Learner.query.filter_by(status='active').all()
    
    # Get existing results
    results = {}
    for learner in learners:
        result = ExamResult.query.filter_by(exam_id=exam.id, learner_id=learner.id).first()
        results[learner.id] = result
    
    return render_template('exams/results.html', exam=exam, learners=learners, results=results)


# Assignment Routes
@app.route('/assignments')
@login_required
@role_required('admin', 'teacher')
def assignments():
    """List all assignments"""
    assignments_list = Assignment.query.order_by(Assignment.assignment_date.desc()).all()
    return render_template('assignments/list.html', assignments=assignments_list)


@app.route('/assignments/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_assignment():
    """Create a new assignment"""
    if request.method == 'POST':
        try:
            assignment = Assignment(
                name=request.form.get('name'),
                subject_id=int(request.form.get('subject_id')),
                class_id=int(request.form.get('class_id')) if request.form.get('class_id') else None,
                assignment_date=datetime.strptime(request.form.get('assignment_date'), '%Y-%m-%d').date() if request.form.get('assignment_date') else date.today(),
                due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else None,
                max_score=int(request.form.get('max_score', 100)),
                session=request.form.get('session'),
                term=request.form.get('term'),
                description=request.form.get('description'),
                created_by=current_user.id
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    return render_template('assignments/add.html', classes=classes, subjects=subjects)


@app.route('/assignments/<int:id>/results', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def assignment_results(id):
    """Enter assignment results"""
    assignment = Assignment.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            results_data = request.get_json().get('results', [])
            
            for result_data in results_data:
                learner_id = result_data.get('learner_id')
                score = float(result_data.get('score', 0))
                
                # Calculate grade based on Nigerian grading system
                percentage = (score / assignment.max_score) * 100
                if percentage >= 75:
                    grade = 'A'
                    remark = 'Excellent'
                elif percentage >= 65:
                    grade = 'B'
                    remark = 'Very Good'
                elif percentage >= 55:
                    grade = 'C'
                    remark = 'Good'
                elif percentage >= 45:
                    grade = 'D'
                    remark = 'Credit'
                else:
                    grade = 'F'
                    remark = 'Fail'
                
                # Check if result exists
                existing = AssignmentResult.query.filter_by(assignment_id=assignment.id, learner_id=learner_id).first()
                
                if existing:
                    existing.score = score
                    existing.grade = grade
                    existing.remark = remark
                    if result_data.get('submitted_date'):
                        existing.submitted_date = datetime.strptime(result_data.get('submitted_date'), '%Y-%m-%d').date()
                else:
                    result = AssignmentResult(
                        assignment_id=assignment.id,
                        learner_id=learner_id,
                        score=score,
                        grade=grade,
                        remark=remark,
                        submitted_date=datetime.strptime(result_data.get('submitted_date'), '%Y-%m-%d').date() if result_data.get('submitted_date') else date.today()
                    )
                    db.session.add(result)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Results saved successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # Get learners for the assignment
    if assignment.class_id and assignment.class_obj:
        learners = Learner.query.filter_by(current_class=assignment.class_obj.name, status='active').all()
    else:
        learners = Learner.query.filter_by(status='active').all()
    
    # Get existing results
    results = {}
    for learner in learners:
        result = AssignmentResult.query.filter_by(assignment_id=assignment.id, learner_id=learner.id).first()
        results[learner.id] = result
    
    return render_template('assignments/results.html', assignment=assignment, learners=learners, results=results)


@app.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def delete_assignment(id):
    """Delete an assignment"""
    assignment = Assignment.query.get_or_404(id)
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash('Assignment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    
    return redirect(url_for('assignments'))


# Test Routes
@app.route('/tests')
@login_required
@role_required('admin', 'teacher')
def tests():
    """List all tests"""
    tests_list = Test.query.order_by(Test.test_date.desc()).all()
    return render_template('tests/list.html', tests=tests_list)


@app.route('/tests/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_test():
    """Create a new test"""
    if request.method == 'POST':
        try:
            test = Test(
                name=request.form.get('name'),
                subject_id=int(request.form.get('subject_id')),
                class_id=int(request.form.get('class_id')) if request.form.get('class_id') else None,
                test_date=datetime.strptime(request.form.get('test_date'), '%Y-%m-%d').date() if request.form.get('test_date') else date.today(),
                max_score=int(request.form.get('max_score', 100)),
                session=request.form.get('session'),
                term=request.form.get('term'),
                description=request.form.get('description'),
                created_by=current_user.id
            )
            
            db.session.add(test)
            db.session.commit()
            
            flash('Test created successfully!', 'success')
            return redirect(url_for('tests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating test: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    return render_template('tests/add.html', classes=classes, subjects=subjects)


@app.route('/tests/<int:id>/results', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def test_results(id):
    """Enter test results"""
    test = Test.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            results_data = request.get_json().get('results', [])
            
            for result_data in results_data:
                learner_id = result_data.get('learner_id')
                score = float(result_data.get('score', 0))
                
                # Calculate grade based on Nigerian grading system
                percentage = (score / test.max_score) * 100
                if percentage >= 75:
                    grade = 'A'
                    remark = 'Excellent'
                elif percentage >= 65:
                    grade = 'B'
                    remark = 'Very Good'
                elif percentage >= 55:
                    grade = 'C'
                    remark = 'Good'
                elif percentage >= 45:
                    grade = 'D'
                    remark = 'Credit'
                else:
                    grade = 'F'
                    remark = 'Fail'
                
                # Check if result exists
                existing = TestResult.query.filter_by(test_id=test.id, learner_id=learner_id).first()
                
                if existing:
                    existing.score = score
                    existing.grade = grade
                    existing.remark = remark
                else:
                    result = TestResult(
                        test_id=test.id,
                        learner_id=learner_id,
                        score=score,
                        grade=grade,
                        remark=remark
                    )
                    db.session.add(result)
            
            # Calculate positions after saving all results
            db.session.commit()
            
            # Recalculate positions
            all_results = TestResult.query.filter_by(test_id=test.id).order_by(TestResult.score.desc()).all()
            for idx, result in enumerate(all_results, start=1):
                result.position = idx
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Results saved successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # Get learners for the test
    if test.class_id and test.class_obj:
        learners = Learner.query.filter_by(current_class=test.class_obj.name, status='active').all()
    else:
        learners = Learner.query.filter_by(status='active').all()
    
    # Get existing results
    results = {}
    for learner in learners:
        result = TestResult.query.filter_by(test_id=test.id, learner_id=learner.id).first()
        results[learner.id] = result
    
    return render_template('tests/results.html', test=test, learners=learners, results=results)


@app.route('/tests/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def delete_test(id):
    """Delete a test"""
    test = Test.query.get_or_404(id)
    try:
        db.session.delete(test)
        db.session.commit()
        flash('Test deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting test: {str(e)}', 'danger')
    
    return redirect(url_for('tests'))


# Class Routes
@app.route('/classes')
@login_required
@role_required('admin', 'teacher')
def classes():
    classes_list = Class.query.filter_by(status='active').all()
    # Get teacher information for each class
    for class_obj in classes_list:
        if class_obj.class_teacher_id:
            class_obj.teacher = Staff.query.get(class_obj.class_teacher_id)
        else:
            class_obj.teacher = None
    return render_template('classes/list.html', classes=classes_list)


@app.route('/classes/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_class():
    if request.method == 'POST':
        try:
            class_obj = Class(
                name=request.form.get('name'),
                level=request.form.get('level'),
                capacity=int(request.form.get('capacity', 40)),
                class_teacher_id=int(request.form.get('class_teacher_id')) if request.form.get('class_teacher_id') else None,
                session=request.form.get('session')
            )
            
            db.session.add(class_obj)
            db.session.commit()
            
            flash('Class added successfully!', 'success')
            return redirect(url_for('classes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding class: {str(e)}', 'danger')
    
    staff = Staff.query.filter_by(status='active').all()
    return render_template('classes/add.html', staff=staff)


# Subject Routes
@app.route('/subjects')
@login_required
@role_required('admin', 'teacher')
def subjects():
    """List all subjects"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    class_filter = request.args.get('class_id', '')
    
    query = Subject.query
    
    if search:
        query = query.filter(
            db.or_(
                Subject.name.ilike(f'%{search}%'),
                Subject.code.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    if class_filter:
        query = query.filter_by(class_id=class_filter)
    
    subjects_list = query.order_by(Subject.name).all()
    
    # Get classes and teachers for display
    classes = Class.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    
    # Get categories for filter
    categories = db.session.query(Subject.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('subjects/list.html', 
                         subjects=subjects_list, 
                         classes=classes,
                         staff=staff,
                         search=search,
                         category=category,
                         class_filter=class_filter,
                         categories=categories)


@app.route('/subjects/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_subject():
    """Create a new subject"""
    if request.method == 'POST':
        try:
            subject = Subject(
                name=request.form.get('name'),
                code=request.form.get('code').upper(),  # Convert to uppercase
                class_id=int(request.form.get('class_id')) if request.form.get('class_id') else None,
                teacher_id=int(request.form.get('teacher_id')) if request.form.get('teacher_id') else None,
                category=request.form.get('category'),
                credit_hours=int(request.form.get('credit_hours', 1)),
                session=request.form.get('session')
            )
            
            db.session.add(subject)
            db.session.commit()
            
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding subject: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    
    # Nigerian curriculum categories
    categories = [
        'Core Subject',
        'Science Subject',
        'Arts Subject',
        'Commercial Subject',
        'Technical Subject',
        'Elective Subject',
        'Language',
        'Social Studies',
        'Religious Studies',
        'Physical Education',
        'Computer Studies',
        'Agricultural Science',
        'Home Economics',
        'Business Studies',
        'Fine Arts',
        'Music',
        'Drama',
        'Other'
    ]
    
    return render_template('subjects/add.html', classes=classes, staff=staff, categories=categories)


@app.route('/subjects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_subject(id):
    """Edit a subject"""
    subject = Subject.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            subject.name = request.form.get('name')
            subject.code = request.form.get('code').upper()
            subject.class_id = int(request.form.get('class_id')) if request.form.get('class_id') else None
            subject.teacher_id = int(request.form.get('teacher_id')) if request.form.get('teacher_id') else None
            subject.category = request.form.get('category')
            subject.credit_hours = int(request.form.get('credit_hours', 1))
            subject.session = request.form.get('session')
            subject.status = request.form.get('status', 'active')
            
            db.session.commit()
            
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating subject: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    
    # Nigerian curriculum categories
    categories = [
        'Core Subject',
        'Science Subject',
        'Arts Subject',
        'Commercial Subject',
        'Technical Subject',
        'Elective Subject',
        'Language',
        'Social Studies',
        'Religious Studies',
        'Physical Education',
        'Computer Studies',
        'Agricultural Science',
        'Home Economics',
        'Business Studies',
        'Fine Arts',
        'Music',
        'Drama',
        'Other'
    ]
    
    return render_template('subjects/edit.html', subject=subject, classes=classes, staff=staff, categories=categories)


@app.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_subject(id):
    """Delete a subject"""
    subject = Subject.query.get_or_404(id)
    try:
        # Check if subject is used in exams, assignments, or tests
        exam_count = Exam.query.filter_by(subject_id=subject.id).count()
        assignment_count = Assignment.query.filter_by(subject_id=subject.id).count()
        test_count = Test.query.filter_by(subject_id=subject.id).count()
        
        if exam_count > 0 or assignment_count > 0 or test_count > 0:
            flash('Cannot delete subject. It is being used in exams, assignments, or tests. Please deactivate it instead.', 'warning')
            subject.status = 'inactive'
            db.session.commit()
        else:
            db.session.delete(subject)
            db.session.commit()
            flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting subject: {str(e)}', 'danger')
    
    return redirect(url_for('subjects'))


# ==================== TIMETABLE ROUTES ====================

@app.route('/timetables')
@login_required
@role_required('admin', 'teacher')
def timetables():
    """List all timetables"""
    class_filter = request.args.get('class_id', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    
    query = SchoolTimetable.query.filter_by(status='active')
    
    if class_filter:
        query = query.filter_by(class_id=class_filter)
    if session_filter:
        query = query.filter_by(session=session_filter)
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    timetables_list = query.order_by(
        SchoolTimetable.day_of_week,
        SchoolTimetable.period
    ).all()
    
    classes = Class.query.filter_by(status='active').all()
    
    # Get unique sessions and terms
    sessions = db.session.query(SchoolTimetable.session).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(SchoolTimetable.term).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    
    return render_template('timetables/list.html',
                         timetables=timetables_list,
                         classes=classes,
                         class_filter=class_filter,
                         session_filter=session_filter,
                         term_filter=term_filter,
                         sessions=sessions,
                         terms=terms)


@app.route('/timetables/view/<int:class_id>')
@login_required
@role_required('admin', 'teacher', 'learner', 'parent')
def view_timetable(class_id):
    """View timetable for a specific class"""
    class_obj = Class.query.get_or_404(class_id)
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    
    query = SchoolTimetable.query.filter_by(
        class_id=class_id,
        status='active'
    )
    
    if session_filter:
        query = query.filter_by(session=session_filter)
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    timetables = query.order_by(
        SchoolTimetable.day_of_week,
        SchoolTimetable.period
    ).all()
    
    # Organize by day and period
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_grid = {}
    
    for day in days:
        timetable_grid[day] = {}
        for timetable in timetables:
            if timetable.day_of_week == day:
                timetable_grid[day][timetable.period] = timetable
    
    # Get unique sessions and terms
    sessions = db.session.query(SchoolTimetable.session).filter_by(class_id=class_id).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(SchoolTimetable.term).filter_by(class_id=class_id).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    
    return render_template('timetables/view.html',
                         class_obj=class_obj,
                         timetable_grid=timetable_grid,
                         days=days,
                         session_filter=session_filter,
                         term_filter=term_filter,
                         sessions=sessions,
                         terms=terms)


@app.route('/timetables/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_timetable():
    """Add a new timetable entry"""
    if request.method == 'POST':
        try:
            timetable = SchoolTimetable(
                class_id=int(request.form.get('class_id')),
                subject_id=int(request.form.get('subject_id')),
                teacher_id=int(request.form.get('teacher_id')),
                day_of_week=request.form.get('day_of_week'),
                period=int(request.form.get('period')),
                start_time=datetime.strptime(request.form.get('start_time'), '%H:%M').time(),
                end_time=datetime.strptime(request.form.get('end_time'), '%H:%M').time(),
                room=request.form.get('room', ''),
                session=request.form.get('session', ''),
                term=request.form.get('term', ''),
                status='active'
            )
            
            # Check for conflicts
            conflict = SchoolTimetable.query.filter_by(
                class_id=timetable.class_id,
                day_of_week=timetable.day_of_week,
                period=timetable.period,
                session=timetable.session,
                term=timetable.term,
                status='active'
            ).first()
            
            if conflict:
                flash('A timetable entry already exists for this class, day, period, session, and term combination.', 'warning')
                return redirect(url_for('add_timetable'))
            
            db.session.add(timetable)
            db.session.commit()
            
            flash('Timetable entry added successfully!', 'success')
            return redirect(url_for('timetables'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding timetable: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    return render_template('timetables/add.html',
                         classes=classes,
                         subjects=subjects,
                         staff=staff,
                         days=days)


@app.route('/timetables/auto-generate', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def auto_generate_timetable():
    """Auto-generate timetable for classes"""
    if request.method == 'POST':
        try:
            class_id = int(request.form.get('class_id'))
            session = request.form.get('session', '')
            term = request.form.get('term', '')
            periods_per_day = int(request.form.get('periods_per_day', 8))
            period_duration = int(request.form.get('period_duration', 40))  # minutes
            start_time = datetime.strptime(request.form.get('start_time', '08:00'), '%H:%M').time()
            break_period = int(request.form.get('break_period', 4))  # Period number for break
            break_duration = int(request.form.get('break_duration', 20))  # minutes
            
            class_obj = Class.query.get_or_404(class_id)
            
            # Get all subjects for this class
            subjects = Subject.query.filter_by(
                class_id=class_id,
                status='active'
            ).all()
            
            if not subjects:
                flash('No subjects found for this class. Please add subjects first.', 'warning')
                return redirect(url_for('auto_generate_timetable'))
            
            # Delete existing timetable for this class, session, and term
            SchoolTimetable.query.filter_by(
                class_id=class_id,
                session=session,
                term=term
            ).delete()
            
            # Generate timetable
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            period_num = 1
            current_time = start_time
            
            # Calculate time slots
            time_slots = []
            for p in range(1, periods_per_day + 1):
                start = current_time
                # Add break duration if this is break period
                if p == break_period:
                    end = add_time_minutes(start, period_duration + break_duration)
                else:
                    end = add_time_minutes(start, period_duration)
                time_slots.append((start, end))
                current_time = end
                period_num += 1
            
            # Distribute subjects across days and periods
            subject_index = 0
            for day in days:
                period_num = 1
                for period_start, period_end in time_slots:
                    if period_num == break_period:
                        # Skip break period
                        period_num += 1
                        continue
                    
                    if subject_index < len(subjects):
                        subject = subjects[subject_index]
                        
                        timetable = SchoolTimetable(
                            class_id=class_id,
                            subject_id=subject.id,
                            teacher_id=subject.teacher_id if subject.teacher_id else None,
                            day_of_week=day,
                            period=period_num,
                            start_time=period_start,
                            end_time=period_end,
                            session=session,
                            term=term,
                            status='active'
                        )
                        
                        db.session.add(timetable)
                        subject_index = (subject_index + 1) % len(subjects)
                    
                    period_num += 1
            
            db.session.commit()
            flash(f'Timetable auto-generated successfully for {class_obj.name}!', 'success')
            return redirect(url_for('view_timetable', class_id=class_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error generating timetable: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error generating timetable: {traceback.format_exc()}')
    
    classes = Class.query.filter_by(status='active').all()
    return render_template('timetables/auto_generate.html', classes=classes)


def add_time_minutes(time_obj, minutes):
    """Add minutes to a time object"""
    from datetime import datetime, timedelta
    dt = datetime.combine(date.today(), time_obj)
    dt += timedelta(minutes=minutes)
    return dt.time()


@app.route('/timetables/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_timetable(id):
    """Edit a timetable entry"""
    timetable = SchoolTimetable.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            timetable.class_id = int(request.form.get('class_id'))
            timetable.subject_id = int(request.form.get('subject_id'))
            timetable.teacher_id = int(request.form.get('teacher_id'))
            timetable.day_of_week = request.form.get('day_of_week')
            timetable.period = int(request.form.get('period'))
            timetable.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
            timetable.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
            timetable.room = request.form.get('room', '')
            timetable.session = request.form.get('session', '')
            timetable.term = request.form.get('term', '')
            timetable.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Timetable entry updated successfully!', 'success')
            return redirect(url_for('timetables'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating timetable: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    return render_template('timetables/edit.html',
                         timetable=timetable,
                         classes=classes,
                         subjects=subjects,
                         staff=staff,
                         days=days)


@app.route('/timetables/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_timetable(id):
    """Delete a timetable entry"""
    timetable = SchoolTimetable.query.get_or_404(id)
    try:
        db.session.delete(timetable)
        db.session.commit()
        flash('Timetable entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting timetable: {str(e)}', 'danger')
    
    return redirect(url_for('timetables'))


# ==================== EXAM TIMETABLE ROUTES ====================

@app.route('/exam-timetables')
@login_required
@role_required('admin', 'teacher')
def exam_timetables():
    """List all exam timetables"""
    class_filter = request.args.get('class_id', '')
    exam_type_filter = request.args.get('exam_type', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    
    query = ExamTimetable.query
    
    if class_filter:
        query = query.filter_by(class_id=class_filter)
    if exam_type_filter:
        query = query.filter_by(exam_type=exam_type_filter)
    if session_filter:
        query = query.filter_by(session=session_filter)
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    exam_timetables_list = query.order_by(
        ExamTimetable.exam_date,
        ExamTimetable.start_time
    ).all()
    
    classes = Class.query.filter_by(status='active').all()
    
    # Get unique exam types, sessions, and terms
    exam_types = db.session.query(ExamTimetable.exam_type).distinct().all()
    exam_types = [et[0] for et in exam_types if et[0]]
    sessions = db.session.query(ExamTimetable.session).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(ExamTimetable.term).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    
    return render_template('exam_timetables/list.html',
                         exam_timetables=exam_timetables_list,
                         classes=classes,
                         class_filter=class_filter,
                         exam_type_filter=exam_type_filter,
                         session_filter=session_filter,
                         term_filter=term_filter,
                         exam_types=exam_types,
                         sessions=sessions,
                         terms=terms)


@app.route('/exam-timetables/view/<int:class_id>')
@login_required
@role_required('admin', 'teacher', 'learner', 'parent')
def view_exam_timetable(class_id):
    """View exam timetable for a specific class"""
    class_obj = Class.query.get_or_404(class_id)
    exam_type_filter = request.args.get('exam_type', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    
    query = ExamTimetable.query.filter_by(class_id=class_id)
    
    if exam_type_filter:
        query = query.filter_by(exam_type=exam_type_filter)
    if session_filter:
        query = query.filter_by(session=session_filter)
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    exam_timetables = query.order_by(
        ExamTimetable.exam_date,
        ExamTimetable.start_time
    ).all()
    
    # Get unique exam types, sessions, and terms
    exam_types = db.session.query(ExamTimetable.exam_type).filter_by(class_id=class_id).distinct().all()
    exam_types = [et[0] for et in exam_types if et[0]]
    sessions = db.session.query(ExamTimetable.session).filter_by(class_id=class_id).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(ExamTimetable.term).filter_by(class_id=class_id).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    
    return render_template('exam_timetables/view.html',
                         class_obj=class_obj,
                         exam_timetables=exam_timetables,
                         exam_type_filter=exam_type_filter,
                         session_filter=session_filter,
                         term_filter=term_filter,
                         exam_types=exam_types,
                         sessions=sessions,
                         terms=terms)


@app.route('/exam-timetables/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_exam_timetable():
    """Add a new exam timetable entry"""
    if request.method == 'POST':
        try:
            start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
            end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
            
            # Calculate duration
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = datetime.combine(date.today(), end_time)
            duration = int((end_dt - start_dt).total_seconds() / 60)
            
            exam_timetable = ExamTimetable(
                exam_name=request.form.get('exam_name'),
                exam_type=request.form.get('exam_type'),
                class_id=int(request.form.get('class_id')),
                subject_id=int(request.form.get('subject_id')),
                exam_date=datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date(),
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                room=request.form.get('room', ''),
                invigilator_id=int(request.form.get('invigilator_id')) if request.form.get('invigilator_id') else None,
                session=request.form.get('session', ''),
                term=request.form.get('term', ''),
                status='scheduled',
                instructions=request.form.get('instructions', '')
            )
            
            db.session.add(exam_timetable)
            db.session.commit()
            
            flash('Exam timetable entry added successfully!', 'success')
            return redirect(url_for('exam_timetables'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding exam timetable: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    
    exam_types = ['Internal', 'WAEC', 'NECO', 'JAMB', 'GCE', 'BECE', 'Other']
    
    return render_template('exam_timetables/add.html',
                         classes=classes,
                         subjects=subjects,
                         staff=staff,
                         exam_types=exam_types)


@app.route('/exam-timetables/auto-generate', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def auto_generate_exam_timetable():
    """Auto-generate exam timetable"""
    if request.method == 'POST':
        try:
            class_id = int(request.form.get('class_id'))
            exam_name = request.form.get('exam_name')
            exam_type = request.form.get('exam_type')
            session = request.form.get('session', '')
            term = request.form.get('term', '')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            exam_duration = int(request.form.get('exam_duration', 120))  # minutes
            start_time = datetime.strptime(request.form.get('start_time', '09:00'), '%H:%M').time()
            exams_per_day = int(request.form.get('exams_per_day', 2))  # Morning and afternoon
            gap_between_exams = int(request.form.get('gap_between_exams', 30))  # minutes
            
            class_obj = Class.query.get_or_404(class_id)
            
            # Get all subjects for this class
            subjects = Subject.query.filter_by(
                class_id=class_id,
                status='active'
            ).all()
            
            if not subjects:
                flash('No subjects found for this class. Please add subjects first.', 'warning')
                return redirect(url_for('auto_generate_exam_timetable'))
            
            # Delete existing exam timetable for this class, exam type, session, and term
            ExamTimetable.query.filter_by(
                class_id=class_id,
                exam_type=exam_type,
                session=session,
                term=term
            ).delete()
            
            # Generate exam timetable
            current_date = start_date
            subject_index = 0
            exam_slot = 0  # 0 for morning, 1 for afternoon
            
            for subject in subjects:
                if exam_slot == 0:
                    # Morning exam
                    exam_start = start_time
                else:
                    # Afternoon exam - calculate after morning exam + gap
                    morning_end = add_time_minutes(start_time, exam_duration)
                    exam_start = add_time_minutes(morning_end, gap_between_exams)
                
                exam_end = add_time_minutes(exam_start, exam_duration)
                
                exam_timetable = ExamTimetable(
                    exam_name=exam_name,
                    exam_type=exam_type,
                    class_id=class_id,
                    subject_id=subject.id,
                    exam_date=current_date,
                    start_time=exam_start,
                    end_time=exam_end,
                    duration=exam_duration,
                    session=session,
                    term=term,
                    status='scheduled'
                )
                
                db.session.add(exam_timetable)
                
                exam_slot += 1
                if exam_slot >= exams_per_day:
                    exam_slot = 0
                    # Move to next day
                    current_date += timedelta(days=1)
                    # Skip weekends
                    while current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                        current_date += timedelta(days=1)
            
            db.session.commit()
            flash(f'Exam timetable auto-generated successfully for {class_obj.name}!', 'success')
            return redirect(url_for('view_exam_timetable', class_id=class_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error generating exam timetable: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error generating exam timetable: {traceback.format_exc()}')
    
    classes = Class.query.filter_by(status='active').all()
    exam_types = ['Internal', 'WAEC', 'NECO', 'JAMB', 'GCE', 'BECE', 'Other']
    
    return render_template('exam_timetables/auto_generate.html',
                         classes=classes,
                         exam_types=exam_types)


@app.route('/exam-timetables/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_exam_timetable(id):
    """Edit an exam timetable entry"""
    exam_timetable = ExamTimetable.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            exam_timetable.exam_name = request.form.get('exam_name')
            exam_timetable.exam_type = request.form.get('exam_type')
            exam_timetable.class_id = int(request.form.get('class_id'))
            exam_timetable.subject_id = int(request.form.get('subject_id'))
            exam_timetable.exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
            exam_timetable.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
            exam_timetable.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
            
            # Calculate duration
            start_dt = datetime.combine(date.today(), exam_timetable.start_time)
            end_dt = datetime.combine(date.today(), exam_timetable.end_time)
            exam_timetable.duration = int((end_dt - start_dt).total_seconds() / 60)
            
            exam_timetable.room = request.form.get('room', '')
            exam_timetable.invigilator_id = int(request.form.get('invigilator_id')) if request.form.get('invigilator_id') else None
            exam_timetable.session = request.form.get('session', '')
            exam_timetable.term = request.form.get('term', '')
            exam_timetable.status = request.form.get('status', 'scheduled')
            exam_timetable.instructions = request.form.get('instructions', '')
            exam_timetable.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Exam timetable entry updated successfully!', 'success')
            return redirect(url_for('exam_timetables'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating exam timetable: {str(e)}', 'danger')
    
    classes = Class.query.filter_by(status='active').all()
    subjects = Subject.query.filter_by(status='active').all()
    staff = Staff.query.filter_by(status='active').all()
    exam_types = ['Internal', 'WAEC', 'NECO', 'JAMB', 'GCE', 'BECE', 'Other']
    
    return render_template('exam_timetables/edit.html',
                         exam_timetable=exam_timetable,
                         classes=classes,
                         subjects=subjects,
                         staff=staff,
                         exam_types=exam_types)


@app.route('/exam-timetables/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_exam_timetable(id):
    """Delete an exam timetable entry"""
    exam_timetable = ExamTimetable.query.get_or_404(id)
    try:
        db.session.delete(exam_timetable)
        db.session.commit()
        flash('Exam timetable entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting exam timetable: {str(e)}', 'danger')
    
    return redirect(url_for('exam_timetables'))


# ==================== E-WALLET ROUTES ====================

def get_or_create_ewallet(user_id):
    """Get or create e-wallet for user"""
    ewallet = EWallet.query.filter_by(user_id=user_id).first()
    if not ewallet:
        ewallet = EWallet(user_id=user_id, balance=0.00, currency='NGN', status='active')
        db.session.add(ewallet)
        db.session.commit()
    return ewallet


@app.route('/ewallet')
@login_required
def ewallet():
    """View e-wallet balance and recent transactions"""
    ewallet = get_or_create_ewallet(current_user.id)
    
    # Get recent transactions
    recent_transactions = EWalletTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(EWalletTransaction.created_at.desc()).limit(10).all()
    
    # Get transaction statistics
    total_deposits = db.session.query(db.func.sum(EWalletTransaction.amount)).filter_by(
        user_id=current_user.id,
        transaction_type='deposit',
        status='completed'
    ).scalar() or 0
    
    total_withdrawals = db.session.query(db.func.sum(EWalletTransaction.amount)).filter_by(
        user_id=current_user.id,
        transaction_type='withdrawal',
        status='completed'
    ).scalar() or 0
    
    total_payments = db.session.query(db.func.sum(EWalletTransaction.amount)).filter_by(
        user_id=current_user.id,
        transaction_type='payment',
        status='completed'
    ).scalar() or 0
    
    return render_template('ewallet/index.html',
                         ewallet=ewallet,
                         recent_transactions=recent_transactions,
                         total_deposits=total_deposits,
                         total_withdrawals=total_withdrawals,
                         total_payments=total_payments)


@app.route('/ewallet/deposit', methods=['GET', 'POST'])
@login_required
def ewallet_deposit():
    """Deposit funds to e-wallet via Flutterwave"""
    ewallet = get_or_create_ewallet(current_user.id)
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            
            if amount < 100:  # Minimum deposit of ₦100
                flash('Minimum deposit amount is ₦100', 'warning')
                return redirect(url_for('ewallet_deposit'))
            
            if amount > 1000000:  # Maximum deposit of ₦1,000,000
                flash('Maximum deposit amount is ₦1,000,000', 'warning')
                return redirect(url_for('ewallet_deposit'))
            
            # Generate unique transaction reference
            tx_ref = f"EWALLET_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
            
            # Create pending transaction
            transaction = EWalletTransaction(
                ewallet_id=ewallet.id,
                user_id=current_user.id,
                transaction_type='deposit',
                amount=amount,
                balance_before=ewallet.balance,
                balance_after=ewallet.balance,  # Will update after payment
                currency='NGN',
                status='pending',
                payment_method='flutterwave',
                payment_gateway='flutterwave',
                transaction_reference=tx_ref,
                flutterwave_tx_ref=tx_ref,
                description=f'Wallet deposit of ₦{amount:,.2f}'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Get Flutterwave configuration
            flutterwave_public_key = app.config.get('FLUTTERWAVE_PUBLIC_KEY', '')
            flutterwave_secret_key = app.config.get('FLUTTERWAVE_SECRET_KEY', '')
            flutterwave_encryption_key = app.config.get('FLUTTERWAVE_ENCRYPTION_KEY', '')
            
            if not flutterwave_public_key or not flutterwave_secret_key:
                flash('Payment gateway not configured. Please contact administrator.', 'danger')
                transaction.status = 'failed'
                db.session.commit()
                return redirect(url_for('ewallet'))
            
            # Prepare Flutterwave payment data
            callback_url = url_for('ewallet_flutterwave_callback', _external=True)
            
            return render_template('ewallet/flutterwave_payment.html',
                                 transaction=transaction,
                                 amount=amount,
                                 tx_ref=tx_ref,
                                 public_key=flutterwave_public_key,
                                 callback_url=callback_url,
                                 user_email=current_user.email,
                                 user_name=f"{current_user.first_name} {current_user.last_name}")
        except Exception as e:
            db.session.rollback()
            flash(f'Error initiating deposit: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error initiating deposit: {traceback.format_exc()}')
    
    return render_template('ewallet/deposit.html', ewallet=ewallet)


@app.route('/ewallet/flutterwave/callback', methods=['POST', 'GET'])
def ewallet_flutterwave_callback():
    """Handle Flutterwave payment callback"""
    try:
        if request.method == 'GET':
            # Handle redirect from Flutterwave
            tx_ref = request.args.get('tx_ref')
            status = request.args.get('status')
            
            if tx_ref:
                transaction = EWalletTransaction.query.filter_by(
                    flutterwave_tx_ref=tx_ref
                ).first()
                
                if transaction:
                    if status == 'successful':
                        # Verify payment with Flutterwave
                        if current_user.is_authenticated:
                            return redirect(url_for('ewallet_verify_payment', tx_ref=tx_ref))
                        else:
                            # User not logged in, redirect to login then verify
                            from flask_login import login_user
                            login_user(transaction.user)
                            return redirect(url_for('ewallet_verify_payment', tx_ref=tx_ref))
                    else:
                        transaction.status = 'failed'
                        db.session.commit()
                        if current_user.is_authenticated:
                            flash('Payment was not successful. Please try again.', 'warning')
                            return redirect(url_for('ewallet'))
                        else:
                            return redirect(url_for('login'))
            
            if current_user.is_authenticated:
                return redirect(url_for('ewallet'))
            else:
                return redirect(url_for('login'))
        
        # Handle webhook from Flutterwave
        import requests
        import hashlib
        import hmac
        
        flutterwave_secret_key = app.config.get('FLUTTERWAVE_SECRET_KEY', '')
        
        if not flutterwave_secret_key:
            return jsonify({'status': 'error', 'message': 'Secret key not configured'}), 400
        
        # Verify webhook signature
        signature = request.headers.get('verif-hash')
        if signature:
            computed_hash = hashlib.sha256((request.data.decode() + flutterwave_secret_key).encode()).hexdigest()
            if signature != computed_hash:
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
        
        data = request.get_json()
        
        if data and data.get('event') == 'charge.completed':
            tx_ref = data.get('data', {}).get('tx_ref')
            tx_id = data.get('data', {}).get('id')
            status = data.get('data', {}).get('status')
            amount = float(data.get('data', {}).get('amount', 0))
            
            transaction = EWalletTransaction.query.filter_by(flutterwave_tx_ref=tx_ref).first()
            
            if transaction and transaction.status == 'pending':
                if status == 'successful':
                    # Update wallet balance
                    ewallet = transaction.ewallet
                    transaction.balance_before = ewallet.balance
                    ewallet.balance += amount
                    transaction.balance_after = ewallet.balance
                    transaction.status = 'completed'
                    transaction.flutterwave_tx_id = str(tx_id)
                    ewallet.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                    
                    # Send notification email
                    try:
                        msg = Message(
                            subject='E-Wallet Deposit Successful',
                            recipients=[transaction.user.email],
                            body=f'Your deposit of ₦{amount:,.2f} has been credited to your e-wallet. New balance: ₦{ewallet.balance:,.2f}'
                        )
                        mail.send(msg)
                    except:
                        pass
                else:
                    transaction.status = 'failed'
                    db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        app.logger.error(f'Error in Flutterwave callback: {traceback.format_exc()}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/ewallet/verify-payment/<tx_ref>')
@login_required
def ewallet_verify_payment(tx_ref):
    """Verify Flutterwave payment status"""
    try:
        transaction = EWalletTransaction.query.filter_by(
            flutterwave_tx_ref=tx_ref,
            user_id=current_user.id
        ).first_or_404()
        
        if transaction.status == 'completed':
            flash('Payment verified successfully!', 'success')
            return redirect(url_for('ewallet'))
        
        # Verify with Flutterwave API
        import requests
        
        flutterwave_secret_key = app.config.get('FLUTTERWAVE_SECRET_KEY', '')
        
        if not flutterwave_secret_key:
            flash('Payment gateway not configured.', 'danger')
            return redirect(url_for('ewallet'))
        
        # Get transaction from Flutterwave
        headers = {
            'Authorization': f'Bearer {flutterwave_secret_key}',
            'Content-Type': 'application/json'
        }
        
        # Use tx_ref to verify if tx_id is not available
        if transaction.flutterwave_tx_id:
            verify_url = f'https://api.flutterwave.com/v3/transactions/{transaction.flutterwave_tx_id}/verify'
        else:
            verify_url = f'https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}'
        
        response = requests.get(verify_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('status') == 'successful':
                amount = float(data.get('data', {}).get('amount', 0))
                
                # Update wallet balance
                ewallet = transaction.ewallet
                transaction.balance_before = ewallet.balance
                ewallet.balance += amount
                transaction.balance_after = ewallet.balance
                transaction.status = 'completed'
                transaction.flutterwave_tx_id = str(data.get('data', {}).get('id', ''))
                ewallet.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                flash(f'Payment verified successfully! ₦{amount:,.2f} has been credited to your wallet.', 'success')
                return redirect(url_for('ewallet'))
            else:
                transaction.status = 'failed'
                db.session.commit()
                flash('Payment verification failed. Please contact support.', 'danger')
        else:
            flash('Unable to verify payment. Please try again later.', 'warning')
        
        return redirect(url_for('ewallet'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error verifying payment: {str(e)}', 'danger')
        import traceback
        app.logger.error(f'Error verifying payment: {traceback.format_exc()}')
        return redirect(url_for('ewallet'))


@app.route('/ewallet/withdraw', methods=['GET', 'POST'])
@login_required
def ewallet_withdraw():
    """Withdraw funds from e-wallet"""
    ewallet = get_or_create_ewallet(current_user.id)
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            bank_name = request.form.get('bank_name', '')
            account_number = request.form.get('account_number', '')
            account_name = request.form.get('account_name', '')
            
            if amount <= 0:
                flash('Invalid withdrawal amount', 'danger')
                return redirect(url_for('ewallet_withdraw'))
            
            if amount > float(ewallet.balance):
                flash('Insufficient wallet balance', 'danger')
                return redirect(url_for('ewallet_withdraw'))
            
            if amount < 100:  # Minimum withdrawal
                flash('Minimum withdrawal amount is ₦100', 'warning')
                return redirect(url_for('ewallet_withdraw'))
            
            # Create withdrawal transaction
            tx_ref = f"WITHDRAW_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
            
            transaction = EWalletTransaction(
                ewallet_id=ewallet.id,
                user_id=current_user.id,
                transaction_type='withdrawal',
                amount=amount,
                balance_before=ewallet.balance,
                balance_after=ewallet.balance - amount,
                currency='NGN',
                status='pending',
                payment_method='bank_transfer',
                transaction_reference=tx_ref,
                description=f'Withdrawal to {bank_name} - {account_number}',
                transaction_metadata=json.dumps({
                    'bank_name': bank_name,
                    'account_number': account_number,
                    'account_name': account_name
                })
            )
            
            # Update wallet balance
            ewallet.balance -= amount
            ewallet.updated_at = datetime.utcnow()
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Withdrawal request submitted successfully. It will be processed within 24-48 hours.', 'success')
            return redirect(url_for('ewallet'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing withdrawal: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error processing withdrawal: {traceback.format_exc()}')
    
    return render_template('ewallet/withdraw.html', ewallet=ewallet)


@app.route('/ewallet/transactions')
@login_required
def ewallet_transactions():
    """View all e-wallet transactions"""
    ewallet = get_or_create_ewallet(current_user.id)
    
    # Filters
    transaction_type = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = EWalletTransaction.query.filter_by(user_id=current_user.id)
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(EWalletTransaction.created_at >= date_from_obj)
        except:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(EWalletTransaction.created_at <= date_to_obj)
        except:
            pass
    
    transactions = query.order_by(EWalletTransaction.created_at.desc()).all()
    
    return render_template('ewallet/transactions.html',
                         ewallet=ewallet,
                         transactions=transactions,
                         transaction_type=transaction_type,
                         status_filter=status_filter,
                         date_from=date_from,
                         date_to=date_to)


@app.route('/ewallet/pay-fee/<int:fee_id>', methods=['POST'])
@login_required
def ewallet_pay_fee(fee_id):
    """Pay fee using e-wallet balance"""
    try:
        fee = Fee.query.get_or_404(fee_id)
        ewallet = get_or_create_ewallet(current_user.id)
        
        # Verify user has permission to pay this fee
        if current_user.role == 'learner':
            learner = Learner.query.filter_by(user_id=current_user.id).first()
            if not learner or fee.learner_id != learner.id:
                flash('You do not have permission to pay this fee.', 'danger')
                return redirect(url_for('fees'))
        elif current_user.role == 'parent':
            # Check if fee belongs to user's child
            learner = Learner.query.filter_by(
                parent_email=current_user.email
            ).first()
            if not learner or fee.learner_id != learner.id:
                flash('You do not have permission to pay this fee.', 'danger')
                return redirect(url_for('parent_fees'))
        else:
            flash('Only learners and parents can pay fees using e-wallet.', 'danger')
            return redirect(url_for('fees'))
        
        if fee.status == 'paid':
            flash('This fee has already been paid.', 'info')
            return redirect(url_for('fees'))
        
        if float(ewallet.balance) < float(fee.amount):
            flash(f'Insufficient wallet balance. Required: ₦{fee.amount:,.2f}, Available: ₦{ewallet.balance:,.2f}', 'danger')
            return redirect(url_for('ewallet'))
        
        # Create payment transaction
        tx_ref = f"FEEPAY_{fee.id}_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        transaction = EWalletTransaction(
            ewallet_id=ewallet.id,
            user_id=current_user.id,
            transaction_type='payment',
            amount=fee.amount,
            balance_before=ewallet.balance,
            balance_after=ewallet.balance - fee.amount,
            currency='NGN',
            status='completed',
            payment_method='ewallet',
            transaction_reference=tx_ref,
            description=f'Fee payment: {fee.fee_type}',
            related_fee_id=fee.id
        )
        
        # Update wallet balance
        ewallet.balance -= fee.amount
        ewallet.updated_at = datetime.utcnow()
        
        # Update fee status
        fee.status = 'paid'
        fee.paid_date = date.today()
        fee.payment_method = 'ewallet'
        fee.receipt_number = tx_ref
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            transaction_reference=tx_ref,
            payment_type='fee',
            learner_id=fee.learner_id,
            fee_id=fee.id,
            amount=fee.amount,
            currency='NGN',
            payment_method='ewallet',
            status='completed',
            payer_name=f"{current_user.first_name} {current_user.last_name}",
            payer_email=current_user.email,
            payer_phone=current_user.phone or '',
            payment_date=datetime.utcnow()
        )
        
        transaction.related_payment_transaction_id = payment_transaction.id
        
        db.session.add(transaction)
        db.session.add(payment_transaction)
        db.session.commit()
        
        flash(f'Fee paid successfully using e-wallet! Receipt: {tx_ref}', 'success')
        return redirect(url_for('ewallet'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing payment: {str(e)}', 'danger')
        import traceback
        app.logger.error(f'Error processing e-wallet fee payment: {traceback.format_exc()}')
        return redirect(url_for('ewallet'))


@app.route('/admin/ewallet/manage', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_manage_ewallet():
    """Admin route to fund user wallets"""
    if request.method == 'POST':
        try:
            user_id = int(request.form.get('user_id'))
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', 'Admin wallet funding').strip()
            
            if amount <= 0:
                flash('Amount must be greater than zero.', 'danger')
                return redirect(url_for('admin_manage_ewallet'))
            
            # Get user
            user = User.query.get_or_404(user_id)
            
            # Get or create wallet
            ewallet = get_or_create_ewallet(user_id)
            
            # Create transaction
            tx_ref = f"ADMIN_FUND_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
            
            balance_before = float(ewallet.balance)
            balance_after = balance_before + amount
            
            transaction = EWalletTransaction(
                ewallet_id=ewallet.id,
                user_id=user_id,
                transaction_type='deposit',
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                currency='NGN',
                status='completed',
                payment_method='admin',
                transaction_reference=tx_ref,
                description=description or f'Admin wallet funding: {description}'
            )
            
            # Update wallet balance
            ewallet.balance = balance_after
            ewallet.updated_at = datetime.utcnow()
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Successfully funded wallet for {user.first_name} {user.last_name} with ₦{amount:,.2f}', 'success')
            return redirect(url_for('admin_manage_ewallet'))
            
        except ValueError:
            flash('Invalid amount or user ID.', 'danger')
            return redirect(url_for('admin_manage_ewallet'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error funding wallet: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error funding wallet: {traceback.format_exc()}')
            return redirect(url_for('admin_manage_ewallet'))
    
    # Get all users with wallets
    wallets = EWallet.query.order_by(EWallet.updated_at.desc()).all()
    
    # Get all users (for dropdown)
    users = User.query.filter(User.role.in_(['learner', 'parent'])).order_by(User.first_name, User.last_name).all()
    
    # Get total wallet statistics
    total_balance = db.session.query(db.func.sum(EWallet.balance)).scalar() or 0
    total_wallets = EWallet.query.count()
    active_wallets = EWallet.query.filter_by(status='active').count()
    
    return render_template('admin/ewallet_manage.html',
                         wallets=wallets,
                         users=users,
                         total_balance=total_balance,
                         total_wallets=total_wallets,
                         active_wallets=active_wallets)


# Reports Routes
@app.route('/reports')
@login_required
@role_required('admin')
def reports():
    return render_template('reports/index.html')


@app.route('/reports/parents')
@login_required
@role_required('admin', 'teacher')
def parent_reports():
    """Generate parent/guardian reports"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # Get unique parents with their children count
    query = db.session.query(
        Learner.parent_name,
        Learner.parent_phone,
        Learner.parent_email,
        Learner.parent_address,
        db.func.count(Learner.id).label('children_count'),
        db.func.group_concat(Learner.admission_number).label('admission_numbers'),
        db.func.group_concat(
            db.case(
                (Learner.current_class.isnot(None), Learner.current_class),
                else_='N/A'
            )
        ).label('classes')
    ).filter(
        Learner.status == 'active',
        Learner.parent_name.isnot(None),
        Learner.parent_name != ''
    )
    
    if search:
        query = query.filter(
            db.or_(
                Learner.parent_name.ilike(f'%{search}%'),
                Learner.parent_phone.ilike(f'%{search}%'),
                Learner.parent_email.ilike(f'%{search}%')
            )
        )
    
    # Group by parent information
    query = query.group_by(
        Learner.parent_name,
        Learner.parent_phone,
        Learner.parent_email,
        Learner.parent_address
    )
    
    # Get all parents with their children details
    parents_data = []
    parent_groups = query.all()
    
    for parent_group in parent_groups:
        # Get all learners for this parent
        learners = Learner.query.filter(
            Learner.status == 'active',
            Learner.parent_name == parent_group.parent_name,
            Learner.parent_phone == parent_group.parent_phone
        ).all()
        
        # Get children details
        children_details = []
        for learner in learners:
            children_details.append({
                'admission_number': learner.admission_number,
                'name': f"{learner.user.first_name} {learner.user.last_name}",
                'class': learner.current_class or 'N/A',
                'gender': learner.gender
            })
        
        parents_data.append({
            'parent_name': parent_group.parent_name,
            'parent_phone': parent_group.parent_phone or 'N/A',
            'parent_email': parent_group.parent_email or 'N/A',
            'parent_address': parent_group.parent_address or 'N/A',
            'children_count': parent_group.children_count,
            'children': children_details
        })
    
    # Sort by children count (descending)
    parents_data.sort(key=lambda x: x['children_count'], reverse=True)
    
    # Pagination
    from math import ceil
    per_page = 20
    total = len(parents_data)
    total_pages = ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_parents = parents_data[start:end]
    
    # Statistics
    total_parents = len(parents_data)
    total_children = sum([p['children_count'] for p in parents_data])
    parents_with_multiple = len([p for p in parents_data if p['children_count'] > 1])
    parents_with_single = len([p for p in parents_data if p['children_count'] == 1])
    
    stats = {
        'total_parents': total_parents,
        'total_children': total_children,
        'parents_with_multiple': parents_with_multiple,
        'parents_with_single': parents_with_single,
        'average_children_per_parent': round(total_children / total_parents, 2) if total_parents > 0 else 0
    }
    
    return render_template('reports/parents.html', parents=paginated_parents, search=search,
                          stats=stats, page=page, total_pages=total_pages, total=total, settings=get_school_settings())


@app.route('/reports/learners')
@login_required
@role_required('admin')
def learner_reports():
    """Generate learner reports with filtering options"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    status_filter = request.args.get('status', 'active')
    
    query = Learner.query.join(User).filter(User.is_active == True)
    
    if search:
        query = query.filter(
            db.or_(
                Learner.admission_number.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    if class_filter:
        query = query.filter(Learner.current_class == class_filter)
    
    if status_filter:
        query = query.filter(Learner.status == status_filter)
    
    learners = query.order_by(Learner.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    classes = Class.query.filter_by(status='active').all()
    
    # Statistics
    total_learners = Learner.query.filter_by(status='active').count()
    total_by_class = db.session.query(Learner.current_class, db.func.count(Learner.id)).filter_by(status='active').group_by(Learner.current_class).all()
    
    return render_template('reports/learners.html', learners=learners, classes=classes, 
                          search=search, class_filter=class_filter, status_filter=status_filter,
                          total_learners=total_learners, total_by_class=total_by_class, settings=get_school_settings())


@app.route('/reports/attendance')
@login_required
@role_required('admin')
def attendance_reports():
    """Generate attendance reports with filtering options"""
    class_filter = request.args.get('class', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = date.today().replace(day=1).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except:
        start = date.today().replace(day=1)
        end = date.today()
    
    # Get attendance data
    query = Attendance.query.filter(Attendance.date >= start, Attendance.date <= end)
    
    if class_filter:
        learners_in_class = Learner.query.filter_by(current_class=class_filter).all()
        learner_ids = [l.id for l in learners_in_class]
        query = query.filter(Attendance.learner_id.in_(learner_ids))
    
    attendances = query.order_by(Attendance.date.desc()).all()
    
    # Calculate statistics
    total_days = (end - start).days + 1
    present_count = Attendance.query.filter(Attendance.date >= start, Attendance.date <= end, Attendance.status == 'present').count()
    absent_count = Attendance.query.filter(Attendance.date >= start, Attendance.date <= end, Attendance.status == 'absent').count()
    late_count = Attendance.query.filter(Attendance.date >= start, Attendance.date <= end, Attendance.status == 'late').count()
    
    # Attendance by learner
    # Use select_from to explicitly specify the base table and join order
    base_query = db.session.query(Learner).join(User, Learner.user_id == User.id)
    
    if class_filter:
        base_query = base_query.filter(Learner.current_class == class_filter)
    
    # Get all learners first
    learners_list = base_query.filter(Learner.status == 'active').all()
    
    # Calculate attendance for each learner
    attendance_by_learner = []
    for learner in learners_list:
        # Count attendance records for this learner in the date range
        present_days = Attendance.query.filter_by(
            learner_id=learner.id,
            status='present'
        ).filter(
            Attendance.date >= start,
            Attendance.date <= end
        ).count()
        
        absent_days = Attendance.query.filter_by(
            learner_id=learner.id,
            status='absent'
        ).filter(
            Attendance.date >= start,
            Attendance.date <= end
        ).count()
        
        late_days = Attendance.query.filter_by(
            learner_id=learner.id,
            status='late'
        ).filter(
            Attendance.date >= start,
            Attendance.date <= end
        ).count()
        
        attendance_by_learner.append({
            'id': learner.id,
            'admission_number': learner.admission_number,
            'first_name': learner.user.first_name,
            'last_name': learner.user.last_name,
            'current_class': learner.current_class,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days
        })
    
    classes = Class.query.filter_by(status='active').all()
    
    return render_template('reports/attendance.html', attendances=attendances, classes=classes,
                          class_filter=class_filter, start_date=start_date, end_date=end_date,
                          start=start, end=end, total_days=total_days,
                          present_count=present_count, absent_count=absent_count, late_count=late_count,
                          attendance_by_learner=attendance_by_learner, settings=get_school_settings())


@app.route('/reports/academic')
@login_required
@role_required('admin')
def academic_reports():
    """Generate academic performance reports"""
    class_filter = request.args.get('class', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    exam_type_filter = request.args.get('exam_type', '')
    
    # Get exams
    query = Exam.query
    
    if class_filter:
        class_obj = Class.query.filter_by(name=class_filter).first()
        if class_obj:
            query = query.filter_by(class_id=class_obj.id)
    
    if session_filter:
        query = query.filter_by(session=session_filter)
    
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    if exam_type_filter:
        query = query.filter_by(exam_type=exam_type_filter)
    
    exams = query.order_by(Exam.created_at.desc()).all()
    
    # Get exam results
    exam_results = {}
    for exam in exams:
        results = ExamResult.query.filter_by(exam_id=exam.id).all()
        exam_results[exam.id] = results
    
    # Calculate statistics
    total_exams = len(exams)
    total_results = ExamResult.query.count()
    
    # Average scores by class
    avg_by_class = db.session.query(
        Class.name,
        db.func.avg(ExamResult.score).label('avg_score')
    ).join(Exam, Exam.class_id == Class.id).join(ExamResult, ExamResult.exam_id == Exam.id)
    
    if class_filter:
        avg_by_class = avg_by_class.filter(Class.name == class_filter)
    
    avg_by_class = avg_by_class.group_by(Class.name).all()
    
    classes = Class.query.filter_by(status='active').all()
    
    # Get unique sessions and terms
    sessions = db.session.query(Exam.session).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(Exam.term).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    exam_types = db.session.query(Exam.exam_type).distinct().all()
    exam_types = [e[0] for e in exam_types if e[0]]
    
    return render_template('reports/academic.html', exams=exams, exam_results=exam_results,
                          classes=classes, class_filter=class_filter, session_filter=session_filter,
                          term_filter=term_filter, exam_type_filter=exam_type_filter,
                          total_exams=total_exams, total_results=total_results, avg_by_class=avg_by_class,
                          sessions=sessions, terms=terms, exam_types=exam_types)


@app.route('/reports/fees')
@login_required
@role_required('admin', 'accountant')
def fee_reports():
    """Generate fee reports with filtering options"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    fee_type_filter = request.args.get('fee_type', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    
    query = Fee.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if fee_type_filter:
        query = query.filter_by(fee_type=fee_type_filter)
    
    if session_filter:
        query = query.filter_by(session=session_filter)
    
    if term_filter:
        query = query.filter_by(term=term_filter)
    
    fees = query.order_by(Fee.due_date.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Calculate statistics
    total_fees = Fee.query.count()
    total_amount = db.session.query(db.func.sum(Fee.amount)).scalar() or 0
    paid_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
    pending_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
    overdue_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='overdue').scalar() or 0
    
    # Fees by type
    fees_by_type = db.session.query(
        Fee.fee_type,
        db.func.count(Fee.id).label('count'),
        db.func.sum(Fee.amount).label('total')
    ).group_by(Fee.fee_type).all()
    
    # Get unique values for filters
    fee_types = db.session.query(Fee.fee_type).distinct().all()
    fee_types = [f[0] for f in fee_types if f[0]]
    sessions = db.session.query(Fee.session).distinct().all()
    sessions = [s[0] for s in sessions if s[0]]
    terms = db.session.query(Fee.term).distinct().all()
    terms = [t[0] for t in terms if t[0]]
    
    return render_template('reports/fees.html', fees=fees, status_filter=status_filter,
                          fee_type_filter=fee_type_filter, session_filter=session_filter,
                          term_filter=term_filter, total_fees=total_fees, total_amount=total_amount,
                          paid_amount=paid_amount, pending_amount=pending_amount, overdue_amount=overdue_amount,
                          fees_by_type=fees_by_type, fee_types=fee_types, sessions=sessions, terms=terms, settings=get_school_settings())


@app.route('/reports/analytics')
@login_required
@role_required('admin')
def analytics_dashboard():
    """Analytics dashboard with visual insights"""
    # Overall statistics
    total_learners = Learner.query.filter_by(status='active').count()
    total_staff = Staff.query.filter_by(status='active').count()
    total_classes = Class.query.filter_by(status='active').count()
    
    # Attendance statistics
    today = date.today()
    month_start = today.replace(day=1)
    attendance_this_month = Attendance.query.filter(
        Attendance.date >= month_start,
        Attendance.date <= today
    ).count()
    present_this_month = Attendance.query.filter(
        Attendance.date >= month_start,
        Attendance.date <= today,
        Attendance.status == 'present'
    ).count()
    attendance_rate = (present_this_month / attendance_this_month * 100) if attendance_this_month > 0 else 0
    
    # Fee statistics
    total_fees = Fee.query.count()
    paid_fees = Fee.query.filter_by(status='paid').count()
    pending_fees = Fee.query.filter_by(status='pending').count()
    total_fee_amount = db.session.query(db.func.sum(Fee.amount)).scalar() or 0
    paid_fee_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
    
    # Academic statistics
    total_exams = Exam.query.count()
    total_results = ExamResult.query.count()
    avg_score = db.session.query(db.func.avg(ExamResult.score)).scalar() or 0
    
    # Learners by class
    learners_by_class = db.session.query(
        Class.name,
        db.func.count(Learner.id).label('count')
    ).join(Learner, Learner.current_class == Class.name).filter(
        Learner.status == 'active'
    ).group_by(Class.name).all()
    
    # Attendance trend (last 7 days)
    attendance_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        present = Attendance.query.filter_by(date=day, status='present').count()
        absent = Attendance.query.filter_by(date=day, status='absent').count()
        attendance_trend.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%a'),
            'present': present,
            'absent': absent
        })
    
    return render_template('reports/analytics.html', 
                          total_learners=total_learners, total_staff=total_staff, total_classes=total_classes,
                          attendance_this_month=attendance_this_month, present_this_month=present_this_month,
                          attendance_rate=attendance_rate, total_fees=total_fees, paid_fees=paid_fees,
                          pending_fees=pending_fees, total_fee_amount=total_fee_amount, paid_fee_amount=paid_fee_amount,
                          total_exams=total_exams, total_results=total_results, avg_score=avg_score,
                          learners_by_class=learners_by_class, attendance_trend=attendance_trend)


@app.route('/reports/report-cards')
@login_required
@role_required('admin')
def report_cards():
    """Generate comprehensive report cards for learners with assignments, tests, and exams"""
    class_filter = request.args.get('class', '')
    session_filter = request.args.get('session', '')
    term_filter = request.args.get('term', '')
    learner_id = request.args.get('learner_id', '', type=int)
    
    query = Learner.query.filter_by(status='active')
    
    if class_filter:
        query = query.filter_by(current_class=class_filter)
    
    if learner_id:
        query = query.filter_by(id=learner_id)
    
    learners = query.all()
    
    # Get all assessment results (Assignments, Tests, Exams) for each learner
    learner_assessments = {}
    learner_totals = {}
    learner_averages = {}
    learner_positions = {}
    
    # Get all subjects
    all_subjects = Subject.query.all()
    subjects_dict = {s.id: s.name for s in all_subjects}
    
    for learner in learners:
        # Get Assignment Results
        assignment_results = AssignmentResult.query.join(Assignment).filter(AssignmentResult.learner_id == learner.id).all()
        assignment_results = [ar for ar in assignment_results 
                             if (not session_filter or ar.assignment.session == session_filter) and
                                (not term_filter or ar.assignment.term == term_filter)]
        
        # Get Test Results
        test_results = TestResult.query.join(Test).filter(TestResult.learner_id == learner.id).all()
        test_results = [tr for tr in test_results 
                       if (not session_filter or tr.test.session == session_filter) and
                          (not term_filter or tr.test.term == term_filter)]
        
        # Get Exam Results
        exam_results = ExamResult.query.join(Exam).filter(ExamResult.learner_id == learner.id).all()
        exam_results = [er for er in exam_results 
                       if (not session_filter or er.exam.session == session_filter) and
                          (not term_filter or er.exam.term == term_filter)]
        
        # Organize by subject
        subject_scores = {}
        for ar in assignment_results:
            subject_id = ar.assignment.subject_id
            if subject_id not in subject_scores:
                subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
            subject_scores[subject_id]['assignments'].append({
                'name': ar.assignment.name,
                'score': float(ar.score),
                'max_score': ar.assignment.max_score,
                'grade': ar.grade,
                'remark': ar.remark,
                'date': ar.assignment.assignment_date
            })
        
        for tr in test_results:
            subject_id = tr.test.subject_id
            if subject_id not in subject_scores:
                subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
            subject_scores[subject_id]['tests'].append({
                'name': tr.test.name,
                'score': float(tr.score),
                'max_score': tr.test.max_score,
                'grade': tr.grade,
                'remark': tr.remark,
                'position': tr.position,
                'date': tr.test.test_date
            })
        
        for er in exam_results:
            subject_id = er.exam.subject_id
            if subject_id not in subject_scores:
                subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
            subject_scores[subject_id]['exams'].append({
                'name': er.exam.name,
                'score': float(er.score),
                'max_score': er.exam.max_score,
                'grade': er.grade,
                'remark': er.remark,
                'position': er.position,
                'date': er.exam.exam_date
            })
        
        # Calculate totals and averages per subject
        subject_totals = {}
        subject_averages = {}
        
        for subject_id, scores in subject_scores.items():
            # Calculate total score for this subject (sum of all assessments)
            total_score = 0
            total_max = 0
            
            for assignment in scores['assignments']:
                total_score += assignment['score']
                total_max += assignment['max_score']
            
            for test in scores['tests']:
                total_score += test['score']
                total_max += test['max_score']
            
            for exam in scores['exams']:
                total_score += exam['score']
                total_max += exam['max_score']
            
            subject_totals[subject_id] = total_score
            subject_averages[subject_id] = (total_score / total_max * 100) if total_max > 0 else 0
        
        learner_assessments[learner.id] = {
            'subject_scores': subject_scores,
            'subject_totals': subject_totals,
            'subject_averages': subject_averages
        }
        
        # Calculate overall total and average for learner
        overall_total = sum(subject_totals.values())
        overall_average = sum(subject_averages.values()) / len(subject_averages) if subject_averages else 0
        
        learner_totals[learner.id] = overall_total
        learner_averages[learner.id] = overall_average
    
    # Calculate class positions (only if class filter is applied)
    if class_filter:
        # Get all learners in the same class
        class_learners = [l for l in learners if l.current_class == class_filter]
        
        # Sort by total score (descending)
        class_learners_sorted = sorted(class_learners, key=lambda l: learner_totals.get(l.id, 0), reverse=True)
        
        # Assign positions
        for idx, learner in enumerate(class_learners_sorted, start=1):
            learner_positions[learner.id] = idx
    else:
        # If no class filter, set position to None
        for learner in learners:
            learner_positions[learner.id] = None
    
    classes = Class.query.filter_by(status='active').all()
    
    # Get unique sessions and terms from all assessment types
    sessions = set()
    terms = set()
    
    # From assignments
    assignment_sessions = db.session.query(Assignment.session).distinct().all()
    sessions.update([s[0] for s in assignment_sessions if s[0]])
    assignment_terms = db.session.query(Assignment.term).distinct().all()
    terms.update([t[0] for t in assignment_terms if t[0]])
    
    # From tests
    test_sessions = db.session.query(Test.session).distinct().all()
    sessions.update([s[0] for s in test_sessions if s[0]])
    test_terms = db.session.query(Test.term).distinct().all()
    terms.update([t[0] for t in test_terms if t[0]])
    
    # From exams
    exam_sessions = db.session.query(Exam.session).distinct().all()
    sessions.update([s[0] for s in exam_sessions if s[0]])
    exam_terms = db.session.query(Exam.term).distinct().all()
    terms.update([t[0] for t in exam_terms if t[0]])
    
    sessions = sorted(list(sessions))
    terms = sorted(list(terms))
    
    # Get school settings for print header
    school_settings = get_school_settings()
    
    return render_template('reports/report_cards.html', learners=learners, classes=classes,
                          class_filter=class_filter, session_filter=session_filter, term_filter=term_filter,
                          learner_id=learner_id, learner_assessments=learner_assessments,
                          learner_totals=learner_totals, learner_averages=learner_averages,
                          learner_positions=learner_positions, subjects_dict=subjects_dict,
                          sessions=sessions, terms=terms, settings=school_settings)


@app.route('/reports/report-cards/download-pdf')
@login_required
@role_required('admin')
def download_report_card_pdf():
    """Download report cards as PDF"""
    try:
        class_filter = request.args.get('class', '')
        session_filter = request.args.get('session', '')
        term_filter = request.args.get('term', '')
        learner_id = request.args.get('learner_id', '', type=int)
        
        query = Learner.query.filter_by(status='active')
        
        if class_filter:
            query = query.filter_by(current_class=class_filter)
        
        if learner_id:
            query = query.filter_by(id=learner_id)
        
        learners = query.all()
        
        # Get all subjects
        all_subjects = Subject.query.all()
        subjects_dict = {s.id: s.name for s in all_subjects}
        
        # Prepare learners data for PDF generation
        learners_data = []
        learner_totals = {}
        learner_averages = {}
        learner_positions = {}
        
        for learner in learners:
            # Get Assignment Results
            assignment_results = AssignmentResult.query.join(Assignment).filter(AssignmentResult.learner_id == learner.id).all()
            assignment_results = [ar for ar in assignment_results 
                                 if (not session_filter or ar.assignment.session == session_filter) and
                                    (not term_filter or ar.assignment.term == term_filter)]
            
            # Get Test Results
            test_results = TestResult.query.join(Test).filter(TestResult.learner_id == learner.id).all()
            test_results = [tr for tr in test_results 
                           if (not session_filter or tr.test.session == session_filter) and
                              (not term_filter or tr.test.term == term_filter)]
            
            # Get Exam Results
            exam_results = ExamResult.query.join(Exam).filter(ExamResult.learner_id == learner.id).all()
            exam_results = [er for er in exam_results 
                           if (not session_filter or er.exam.session == session_filter) and
                              (not term_filter or er.exam.term == term_filter)]
            
            # Organize by subject
            subject_scores = {}
            for ar in assignment_results:
                subject_id = ar.assignment.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['assignments'].append({
                    'name': ar.assignment.name,
                    'score': float(ar.score),
                    'max_score': ar.assignment.max_score,
                    'grade': ar.grade,
                })
            
            for tr in test_results:
                subject_id = tr.test.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['tests'].append({
                    'name': tr.test.name,
                    'score': float(tr.score),
                    'max_score': tr.test.max_score,
                    'grade': tr.grade,
                })
            
            for er in exam_results:
                subject_id = er.exam.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['exams'].append({
                    'name': er.exam.name,
                    'score': float(er.score),
                    'max_score': er.exam.max_score,
                    'grade': er.grade,
                })
            
            # Calculate totals and averages
            subject_totals = {}
            subject_averages = {}
            
            for subject_id, scores in subject_scores.items():
                total_score = 0
                total_max = 0
                
                for assignment in scores['assignments']:
                    total_score += assignment['score']
                    total_max += assignment['max_score']
                
                for test in scores['tests']:
                    total_score += test['score']
                    total_max += test['max_score']
                
                for exam in scores['exams']:
                    total_score += exam['score']
                    total_max += exam['max_score']
                
                subject_totals[subject_id] = total_score
                subject_averages[subject_id] = (total_score / total_max * 100) if total_max > 0 else 0
            
            overall_total = sum(subject_totals.values())
            overall_average = sum(subject_averages.values()) / len(subject_averages) if subject_averages else 0
            
            learner_totals[learner.id] = overall_total
            learner_averages[learner.id] = overall_average
            
            learners_data.append({
                'learner': learner,
                'assessments': {
                    'subject_scores': subject_scores,
                    'subject_totals': subject_totals,
                    'subject_averages': subject_averages
                },
                'totals': overall_total,
                'averages': overall_average,
                'position': None,  # Will be calculated below
                'subjects_dict': subjects_dict
            })
        
        # Calculate positions
        if class_filter:
            class_learners = [l for l in learners if l.current_class == class_filter]
            class_learners_sorted = sorted(class_learners, key=lambda l: learner_totals.get(l.id, 0), reverse=True)
            for idx, learner in enumerate(class_learners_sorted, start=1):
                learner_positions[learner.id] = idx
                # Update position in learners_data
                for ld in learners_data:
                    if ld['learner'].id == learner.id:
                        ld['position'] = idx
        
        # Get school settings
        school_settings = get_school_settings()
        
        # Construct logo path
        logo_path = ''
        logo_relative = school_settings.get('school_logo', '')
        if logo_relative:
            logo_full_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_relative)
            if os.path.exists(logo_full_path):
                logo_path = logo_full_path
        
        school_info = {
            'school_name': school_settings.get('school_name', 'Wajina International School'),
            'school_address': school_settings.get('school_address', 'Makurdi, Benue State, Nigeria'),
            'school_phone': school_settings.get('school_phone', ''),
            'school_email': school_settings.get('school_email', ''),
            'school_website': school_settings.get('school_website', ''),
            'logo_path': logo_path
        }
        
        filters_dict = {
            'session': session_filter,
            'term': term_filter,
            'class': class_filter
        }
        
        pdf_buffer = generate_report_card_pdf(learners_data, filters_dict, school_info)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'report_cards_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('report_cards'))


@app.route('/reports/report-cards/download-csv')
@login_required
@role_required('admin')
def download_report_card_csv():
    """Download report cards as CSV"""
    try:
        class_filter = request.args.get('class', '')
        session_filter = request.args.get('session', '')
        term_filter = request.args.get('term', '')
        learner_id = request.args.get('learner_id', '', type=int)
        
        query = Learner.query.filter_by(status='active')
        
        if class_filter:
            query = query.filter_by(current_class=class_filter)
        
        if learner_id:
            query = query.filter_by(id=learner_id)
        
        learners = query.all()
        
        # Get all subjects
        all_subjects = Subject.query.all()
        subjects_dict = {s.id: s.name for s in all_subjects}
        
        # Prepare learners data for CSV generation
        learners_data = []
        learner_totals = {}
        
        for learner in learners:
            # Get Assignment Results
            assignment_results = AssignmentResult.query.join(Assignment).filter(AssignmentResult.learner_id == learner.id).all()
            assignment_results = [ar for ar in assignment_results 
                                 if (not session_filter or ar.assignment.session == session_filter) and
                                    (not term_filter or ar.assignment.term == term_filter)]
            
            # Get Test Results
            test_results = TestResult.query.join(Test).filter(TestResult.learner_id == learner.id).all()
            test_results = [tr for tr in test_results 
                           if (not session_filter or tr.test.session == session_filter) and
                              (not term_filter or tr.test.term == term_filter)]
            
            # Get Exam Results
            exam_results = ExamResult.query.join(Exam).filter(ExamResult.learner_id == learner.id).all()
            exam_results = [er for er in exam_results 
                           if (not session_filter or er.exam.session == session_filter) and
                              (not term_filter or er.exam.term == term_filter)]
            
            # Organize by subject
            subject_scores = {}
            for ar in assignment_results:
                subject_id = ar.assignment.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['assignments'].append({
                    'name': ar.assignment.name,
                    'score': float(ar.score),
                    'max_score': ar.assignment.max_score,
                    'grade': ar.grade,
                })
            
            for tr in test_results:
                subject_id = tr.test.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['tests'].append({
                    'name': tr.test.name,
                    'score': float(tr.score),
                    'max_score': tr.test.max_score,
                    'grade': tr.grade,
                })
            
            for er in exam_results:
                subject_id = er.exam.subject_id
                if subject_id not in subject_scores:
                    subject_scores[subject_id] = {'assignments': [], 'tests': [], 'exams': []}
                subject_scores[subject_id]['exams'].append({
                    'name': er.exam.name,
                    'score': float(er.score),
                    'max_score': er.exam.max_score,
                    'grade': er.grade,
                })
            
            # Calculate totals and averages
            subject_totals = {}
            subject_averages = {}
            
            for subject_id, scores in subject_scores.items():
                total_score = 0
                total_max = 0
                
                for assignment in scores['assignments']:
                    total_score += assignment['score']
                    total_max += assignment['max_score']
                
                for test in scores['tests']:
                    total_score += test['score']
                    total_max += test['max_score']
                
                for exam in scores['exams']:
                    total_score += exam['score']
                    total_max += exam['max_score']
                
                subject_totals[subject_id] = total_score
                subject_averages[subject_id] = (total_score / total_max * 100) if total_max > 0 else 0
            
            overall_total = sum(subject_totals.values())
            overall_average = sum(subject_averages.values()) / len(subject_averages) if subject_averages else 0
            
            learner_totals[learner.id] = overall_total
            
            # Calculate position
            position = None
            if class_filter:
                class_learners = [l for l in learners if l.current_class == class_filter]
                class_learners_sorted = sorted(class_learners, key=lambda l: learner_totals.get(l.id, 0), reverse=True)
                for idx, l in enumerate(class_learners_sorted, start=1):
                    if l.id == learner.id:
                        position = idx
                        break
            
            learners_data.append({
                'learner': learner,
                'assessments': {
                    'subject_scores': subject_scores,
                    'subject_totals': subject_totals,
                    'subject_averages': subject_averages
                },
                'totals': overall_total,
                'averages': overall_average,
                'position': position,
                'subjects_dict': subjects_dict
            })
        
        filters_dict = {
            'session': session_filter,
            'term': term_filter,
            'class': class_filter
        }
        
        csv_buffer = generate_report_card_csv(learners_data, filters_dict)
        
        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=report_cards_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    except Exception as e:
        flash(f'Error generating CSV: {str(e)}', 'danger')
        return redirect(url_for('report_cards'))


# User Profile Routes
@app.route('/profile')
@login_required
def profile():
    """View user profile"""
    learner = None
    staff = None
    
    if current_user.role == 'learner':
        learner = Learner.query.filter_by(user_id=current_user.id).first()
    elif current_user.role == 'teacher':
        staff = Staff.query.filter_by(user_id=current_user.id).first()
    
    return render_template('profile/view.html', learner=learner, staff=staff)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Update user information
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.email = request.form.get('email', current_user.email)
            current_user.phone = request.form.get('phone', current_user.phone)
            
            # Update password if provided
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            if new_password:
                if new_password != confirm_password:
                    flash('New password and confirmation password do not match!', 'danger')
                    return redirect(url_for('edit_profile'))
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters long!', 'danger')
                    return redirect(url_for('edit_profile'))
                current_user.set_password(new_password)
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    filename = f"profile_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    current_user.profile_picture = f"profiles/{filename}"
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    learner = None
    staff = None
    
    if current_user.role == 'learner':
        learner = Learner.query.filter_by(user_id=current_user.id).first()
    elif current_user.role == 'teacher':
        staff = Staff.query.filter_by(user_id=current_user.id).first()
    
    return render_template('profile/edit.html', learner=learner, staff=staff)


# App Settings Routes
@app.route('/settings')
@login_required
@role_required('admin')
def settings():
    """View app settings"""
    # Load settings from file if available
    load_settings_from_file()
    
    # Get current settings from app config
    current_settings = {
        # School Information
        'school_name': app.config.get('SCHOOL_NAME', 'Wajina International School'),
        'school_address': app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
        'school_phone': app.config.get('SCHOOL_PHONE', ''),
        'school_email': app.config.get('SCHOOL_EMAIL', ''),
        'school_website': app.config.get('SCHOOL_WEBSITE', ''),
        'school_logo': app.config.get('SCHOOL_LOGO', ''),
        
        # Academic Settings
        'current_session': app.config.get('CURRENT_SESSION', '2024/2025'),
        'current_term': app.config.get('CURRENT_TERM', 'First Term'),
        'session_start_date': app.config.get('SESSION_START_DATE', ''),
        'session_end_date': app.config.get('SESSION_END_DATE', ''),
        'default_class_capacity': app.config.get('DEFAULT_CLASS_CAPACITY', 40),
        'admission_number_format': app.config.get('ADMISSION_NUMBER_FORMAT', 'YEAR-SEQ'),
        
        # Grading System
        'grade_a_min': app.config.get('GRADE_A_MIN', 75),
        'grade_b_min': app.config.get('GRADE_B_MIN', 65),
        'grade_c_min': app.config.get('GRADE_C_MIN', 55),
        'grade_d_min': app.config.get('GRADE_D_MIN', 45),
        'grade_a_label': app.config.get('GRADE_A_LABEL', 'Excellent'),
        'grade_b_label': app.config.get('GRADE_B_LABEL', 'Very Good'),
        'grade_c_label': app.config.get('GRADE_C_LABEL', 'Good'),
        'grade_d_label': app.config.get('GRADE_D_LABEL', 'Credit'),
        'grade_f_label': app.config.get('GRADE_F_LABEL', 'Fail'),
        
        # Feature Toggles
        'enable_online_admission': app.config.get('ENABLE_ONLINE_ADMISSION', True),
        'enable_online_payment': app.config.get('ENABLE_ONLINE_PAYMENT', True),
        'enable_id_cards': app.config.get('ENABLE_ID_CARDS', True),
        'enable_report_cards': app.config.get('ENABLE_REPORT_CARDS', True),
        'enable_assignments': app.config.get('ENABLE_ASSIGNMENTS', True),
        'enable_tests': app.config.get('ENABLE_TESTS', True),
        'enable_exams': app.config.get('ENABLE_EXAMS', True),
        'enable_attendance': app.config.get('ENABLE_ATTENDANCE', True),
        'enable_fees': app.config.get('ENABLE_FEES', True),
        'enable_store': app.config.get('ENABLE_STORE', True),
        'enable_expenditures': app.config.get('ENABLE_EXPENDITURES', True),
        'enable_salaries': app.config.get('ENABLE_SALARIES', True),
        'enable_salary_advances': app.config.get('ENABLE_SALARY_ADVANCES', True),
        
        # Access Control
        'teachers_can_add_learners': app.config.get('TEACHERS_CAN_ADD_LEARNERS', False),
        'teachers_can_add_staff': app.config.get('TEACHERS_CAN_ADD_STAFF', False),
        'teachers_can_create_exams': app.config.get('TEACHERS_CAN_CREATE_EXAMS', True),
        'teachers_can_view_reports': app.config.get('TEACHERS_CAN_VIEW_REPORTS', False),
        'teachers_can_manage_fees': app.config.get('TEACHERS_CAN_MANAGE_FEES', False),
        
        # Display Settings
        'items_per_page': app.config.get('ITEMS_PER_PAGE', 20),
        'date_format': app.config.get('DATE_FORMAT', 'DD/MM/YYYY'),
        'time_format': app.config.get('TIME_FORMAT', '24H'),
        'number_format': app.config.get('NUMBER_FORMAT', 'COMMA'),
        
        # Fee Settings
        'default_fee_types': app.config.get('DEFAULT_FEE_TYPES', 'Tuition,PTA Levy,Library,Laboratory,Sports,Examination,Development Levy'),
        'payment_methods': app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque'),
        'receipt_number_format': app.config.get('RECEIPT_NUMBER_FORMAT', 'REC-YYYYMMDD-SEQ'),
        
        # Report Settings
        'auto_include_logo': app.config.get('AUTO_INCLUDE_LOGO', True),
        'require_signatures': app.config.get('REQUIRE_SIGNATURES', True),
        'default_report_format': app.config.get('DEFAULT_REPORT_FORMAT', 'PDF'),
        
        # Notification Settings
        'enable_notifications': app.config.get('ENABLE_NOTIFICATIONS', True),
        'enable_sms': app.config.get('ENABLE_SMS', False),
        'enable_email': app.config.get('ENABLE_EMAIL', True),
        'notify_fee_payment': app.config.get('NOTIFY_FEE_PAYMENT', True),
        'notify_exam_results': app.config.get('NOTIFY_EXAM_RESULTS', True),
        'notify_attendance': app.config.get('NOTIFY_ATTENDANCE', False),
        
        # Email Configuration
        'mail_server': app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
        'mail_port': app.config.get('MAIL_PORT', 587),
        'mail_username': app.config.get('MAIL_USERNAME', ''),
        'mail_password': app.config.get('MAIL_PASSWORD', ''),
        'mail_default_sender': app.config.get('MAIL_DEFAULT_SENDER', ''),
        'mail_use_tls': app.config.get('MAIL_USE_TLS', True),
        'mail_use_ssl': app.config.get('MAIL_USE_SSL', False),
        
        # Currency Settings
        'currency': app.config.get('CURRENCY', 'NGN'),
        'currency_symbol': app.config.get('CURRENCY_SYMBOL', '₦'),
        
        # Theme Settings
        'app_theme': app.config.get('APP_THEME', 'lemon-green'),
        
        # Security Settings
        'min_password_length': app.config.get('MIN_PASSWORD_LENGTH', 6),
        'require_password_complexity': app.config.get('REQUIRE_PASSWORD_COMPLEXITY', False),
        'session_timeout_minutes': app.config.get('SESSION_TIMEOUT_MINUTES', 60),
        'max_login_attempts': app.config.get('MAX_LOGIN_ATTEMPTS', 5),
        
        # System Settings
        'auto_backup_enabled': app.config.get('AUTO_BACKUP_ENABLED', False),
        'backup_frequency': app.config.get('BACKUP_FREQUENCY', 'daily'),
        'data_retention_days': app.config.get('DATA_RETENTION_DAYS', 365),
        
        # Login Page Settings
        'login_page_title': app.config.get('LOGIN_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'login_welcome_message': app.config.get('LOGIN_WELCOME_MESSAGE', 'Welcome Back'),
        'login_subtitle': app.config.get('LOGIN_SUBTITLE', 'School Management System'),
        'login_show_logo': app.config.get('LOGIN_SHOW_LOGO', True),
        'login_use_logo_as_background': app.config.get('LOGIN_USE_LOGO_AS_BACKGROUND', False),
        'login_logo_background_opacity': app.config.get('LOGIN_LOGO_BACKGROUND_OPACITY', 0.1),
        'login_logo_background_size': app.config.get('LOGIN_LOGO_BACKGROUND_SIZE', 'cover'),
        'login_logo_background_position': app.config.get('LOGIN_LOGO_BACKGROUND_POSITION', 'center'),
        'login_logo_background_repeat': app.config.get('LOGIN_LOGO_BACKGROUND_REPEAT', 'no-repeat'),
        'login_background_image': app.config.get('LOGIN_BACKGROUND_IMAGE', ''),
        'login_background_color': app.config.get('LOGIN_BACKGROUND_COLOR', '#f8f9fa'),
        'login_show_default_credentials': app.config.get('LOGIN_SHOW_DEFAULT_CREDENTIALS', True),
        
        # Landing Page Settings
        'landing_page_title': app.config.get('LANDING_PAGE_TITLE', 'Wajina Suite - School Management System'),
        'landing_hero_title': app.config.get('LANDING_HERO_TITLE', 'Wajina International School'),
        'landing_hero_subtitle': app.config.get('LANDING_HERO_SUBTITLE', 'Comprehensive School Management System'),
        'landing_show_logo': app.config.get('LANDING_SHOW_LOGO', True),
        'landing_show_hero_button': app.config.get('LANDING_SHOW_HERO_BUTTON', True),
        'landing_hero_button_text': app.config.get('LANDING_HERO_BUTTON_TEXT', 'Apply for Admission Online'),
        'landing_show_features': app.config.get('LANDING_SHOW_FEATURES', True),
        'landing_show_portals': app.config.get('LANDING_SHOW_PORTALS', True),
        'landing_background_color': app.config.get('LANDING_BACKGROUND_COLOR', '#9ACD32'),
        'landing_background_image': app.config.get('LANDING_BACKGROUND_IMAGE', ''),
        
        # ID Card Settings
        'id_card_width': app.config.get('ID_CARD_WIDTH', 500),
        'id_card_height': app.config.get('ID_CARD_HEIGHT', 0),
        'id_card_border_radius': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'id_card_bg_color': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'id_card_header_bg_color': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'id_card_footer_bg_color': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'id_card_border_color': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'id_card_border_width': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'id_card_logo_position': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'id_card_logo_height': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'id_card_logo_margin_bottom': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'id_card_photo_position': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'id_card_photo_width': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'id_card_photo_height': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'id_card_photo_border_color': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'id_card_photo_border_width': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'id_card_text_position': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'id_card_name_font_size': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'id_card_label_font_size': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'id_card_value_font_size': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'id_card_text_color': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'id_card_label_color': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'id_card_qr_position': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'id_card_qr_size': app.config.get('ID_CARD_QR_SIZE', 120),
        'id_card_show_qr': app.config.get('ID_CARD_SHOW_QR', True),
        'id_card_header_title_size': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'id_card_header_subtitle_size': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'id_card_header_text_color': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'id_card_footer_text_color': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'id_card_footer_font_size': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    return render_template('settings/index.html', settings=current_settings)


@app.route('/settings/update', methods=['POST'])
@login_required
@role_required('admin')
def update_settings():
    """Update app settings"""
    try:
        # School Information
        app.config['SCHOOL_NAME'] = request.form.get('school_name', '')
        app.config['SCHOOL_ADDRESS'] = request.form.get('school_address', '')
        app.config['SCHOOL_PHONE'] = request.form.get('school_phone', '')
        app.config['SCHOOL_EMAIL'] = request.form.get('school_email', '')
        app.config['SCHOOL_WEBSITE'] = request.form.get('school_website', '')
        
        # Academic Settings
        app.config['CURRENT_SESSION'] = request.form.get('current_session', '')
        app.config['CURRENT_TERM'] = request.form.get('current_term', '')
        app.config['SESSION_START_DATE'] = request.form.get('session_start_date', '')
        app.config['SESSION_END_DATE'] = request.form.get('session_end_date', '')
        app.config['DEFAULT_CLASS_CAPACITY'] = int(request.form.get('default_class_capacity', 40))
        app.config['ADMISSION_NUMBER_FORMAT'] = request.form.get('admission_number_format', 'YEAR-SEQ')
        
        # Grading System
        app.config['GRADE_A_MIN'] = float(request.form.get('grade_a_min', 75))
        app.config['GRADE_B_MIN'] = float(request.form.get('grade_b_min', 65))
        app.config['GRADE_C_MIN'] = float(request.form.get('grade_c_min', 55))
        app.config['GRADE_D_MIN'] = float(request.form.get('grade_d_min', 45))
        app.config['GRADE_A_LABEL'] = request.form.get('grade_a_label', 'Excellent')
        app.config['GRADE_B_LABEL'] = request.form.get('grade_b_label', 'Very Good')
        app.config['GRADE_C_LABEL'] = request.form.get('grade_c_label', 'Good')
        app.config['GRADE_D_LABEL'] = request.form.get('grade_d_label', 'Credit')
        app.config['GRADE_F_LABEL'] = request.form.get('grade_f_label', 'Fail')
        
        # Feature Toggles
        app.config['ENABLE_ONLINE_ADMISSION'] = bool(request.form.get('enable_online_admission'))
        app.config['ENABLE_ONLINE_PAYMENT'] = bool(request.form.get('enable_online_payment'))
        app.config['ENABLE_ID_CARDS'] = bool(request.form.get('enable_id_cards'))
        app.config['ENABLE_REPORT_CARDS'] = bool(request.form.get('enable_report_cards'))
        app.config['ENABLE_ASSIGNMENTS'] = bool(request.form.get('enable_assignments'))
        app.config['ENABLE_TESTS'] = bool(request.form.get('enable_tests'))
        app.config['ENABLE_EXAMS'] = bool(request.form.get('enable_exams'))
        app.config['ENABLE_ATTENDANCE'] = bool(request.form.get('enable_attendance'))
        app.config['ENABLE_FEES'] = bool(request.form.get('enable_fees'))
        app.config['ENABLE_STORE'] = bool(request.form.get('enable_store'))
        app.config['ENABLE_EXPENDITURES'] = bool(request.form.get('enable_expenditures'))
        app.config['ENABLE_SALARIES'] = bool(request.form.get('enable_salaries'))
        app.config['ENABLE_SALARY_ADVANCES'] = bool(request.form.get('enable_salary_advances'))
        
        # Access Control
        app.config['TEACHERS_CAN_ADD_LEARNERS'] = bool(request.form.get('teachers_can_add_learners'))
        app.config['TEACHERS_CAN_ADD_STAFF'] = bool(request.form.get('teachers_can_add_staff'))
        app.config['TEACHERS_CAN_CREATE_EXAMS'] = bool(request.form.get('teachers_can_create_exams'))
        app.config['TEACHERS_CAN_VIEW_REPORTS'] = bool(request.form.get('teachers_can_view_reports'))
        app.config['TEACHERS_CAN_MANAGE_FEES'] = bool(request.form.get('teachers_can_manage_fees'))
        
        # Display Settings
        app.config['ITEMS_PER_PAGE'] = int(request.form.get('items_per_page', 20))
        app.config['DATE_FORMAT'] = request.form.get('date_format', 'DD/MM/YYYY')
        app.config['TIME_FORMAT'] = request.form.get('time_format', '24H')
        app.config['NUMBER_FORMAT'] = request.form.get('number_format', 'COMMA')
        
        # Fee Settings
        app.config['DEFAULT_FEE_TYPES'] = request.form.get('default_fee_types', '')
        app.config['PAYMENT_METHODS'] = request.form.get('payment_methods', '')
        app.config['RECEIPT_NUMBER_FORMAT'] = request.form.get('receipt_number_format', 'REC-YYYYMMDD-SEQ')
        
        # Report Settings
        app.config['AUTO_INCLUDE_LOGO'] = bool(request.form.get('auto_include_logo'))
        app.config['REQUIRE_SIGNATURES'] = bool(request.form.get('require_signatures'))
        app.config['DEFAULT_REPORT_FORMAT'] = request.form.get('default_report_format', 'PDF')
        
        # Notification Settings
        app.config['ENABLE_NOTIFICATIONS'] = bool(request.form.get('enable_notifications'))
        app.config['ENABLE_SMS'] = bool(request.form.get('enable_sms'))
        app.config['ENABLE_EMAIL'] = bool(request.form.get('enable_email'))
        app.config['NOTIFY_FEE_PAYMENT'] = bool(request.form.get('notify_fee_payment'))
        app.config['NOTIFY_EXAM_RESULTS'] = bool(request.form.get('notify_exam_results'))
        app.config['NOTIFY_ATTENDANCE'] = bool(request.form.get('notify_attendance'))
        
        # Email Configuration
        app.config['MAIL_SERVER'] = request.form.get('mail_server', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(request.form.get('mail_port', 587))
        app.config['MAIL_USERNAME'] = request.form.get('mail_username', '')
        app.config['MAIL_PASSWORD'] = request.form.get('mail_password', '')
        app.config['MAIL_DEFAULT_SENDER'] = request.form.get('mail_default_sender', '')
        app.config['MAIL_USE_TLS'] = bool(request.form.get('mail_use_tls'))
        app.config['MAIL_USE_SSL'] = bool(request.form.get('mail_use_ssl'))
        
        # Currency Settings
        app.config['CURRENCY'] = request.form.get('currency', 'NGN')
        app.config['CURRENCY_SYMBOL'] = request.form.get('currency_symbol', '₦')
        
        # Flutterwave Configuration
        app.config['FLUTTERWAVE_PUBLIC_KEY'] = request.form.get('flutterwave_public_key', '')
        app.config['FLUTTERWAVE_SECRET_KEY'] = request.form.get('flutterwave_secret_key', '')
        app.config['FLUTTERWAVE_ENCRYPTION_KEY'] = request.form.get('flutterwave_encryption_key', '')
        app.config['FLUTTERWAVE_ENVIRONMENT'] = request.form.get('flutterwave_environment', 'sandbox')
        
        # Theme Settings
        app.config['APP_THEME'] = request.form.get('app_theme', 'lemon-green')
        
        # Security Settings
        app.config['MIN_PASSWORD_LENGTH'] = int(request.form.get('min_password_length', 6))
        app.config['REQUIRE_PASSWORD_COMPLEXITY'] = bool(request.form.get('require_password_complexity'))
        app.config['SESSION_TIMEOUT_MINUTES'] = int(request.form.get('session_timeout_minutes', 60))
        app.config['MAX_LOGIN_ATTEMPTS'] = int(request.form.get('max_login_attempts', 5))
        
        # System Settings
        app.config['AUTO_BACKUP_ENABLED'] = bool(request.form.get('auto_backup_enabled'))
        app.config['BACKUP_FREQUENCY'] = request.form.get('backup_frequency', 'daily')
        app.config['DATA_RETENTION_DAYS'] = int(request.form.get('data_retention_days', 365))
        
        # Login Page Settings
        app.config['LOGIN_PAGE_TITLE'] = request.form.get('login_page_title', app.config.get('LOGIN_PAGE_TITLE', 'Wajina Suite - School Management System'))
        app.config['LOGIN_WELCOME_MESSAGE'] = request.form.get('login_welcome_message', app.config.get('LOGIN_WELCOME_MESSAGE', 'Welcome Back'))
        app.config['LOGIN_SUBTITLE'] = request.form.get('login_subtitle', app.config.get('LOGIN_SUBTITLE', 'School Management System'))
        app.config['LOGIN_SHOW_LOGO'] = 'login_show_logo' in request.form
        app.config['LOGIN_USE_LOGO_AS_BACKGROUND'] = 'login_use_logo_as_background' in request.form
        app.config['LOGIN_LOGO_BACKGROUND_OPACITY'] = float(request.form.get('login_logo_background_opacity', app.config.get('LOGIN_LOGO_BACKGROUND_OPACITY', 0.1)))
        app.config['LOGIN_LOGO_BACKGROUND_SIZE'] = request.form.get('login_logo_background_size', app.config.get('LOGIN_LOGO_BACKGROUND_SIZE', 'cover'))
        app.config['LOGIN_LOGO_BACKGROUND_POSITION'] = request.form.get('login_logo_background_position', app.config.get('LOGIN_LOGO_BACKGROUND_POSITION', 'center'))
        app.config['LOGIN_LOGO_BACKGROUND_REPEAT'] = request.form.get('login_logo_background_repeat', app.config.get('LOGIN_LOGO_BACKGROUND_REPEAT', 'no-repeat'))
        app.config['LOGIN_BACKGROUND_COLOR'] = request.form.get('login_background_color', app.config.get('LOGIN_BACKGROUND_COLOR', '#f8f9fa'))
        app.config['LOGIN_SHOW_DEFAULT_CREDENTIALS'] = 'login_show_default_credentials' in request.form
        
        # Handle logo upload
        if 'school_logo' in request.files:
            logo_file = request.files['school_logo']
            if logo_file and logo_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in logo_file.filename and logo_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Delete old logo if exists
                    old_logo = app.config.get('SCHOOL_LOGO', '')
                    if old_logo:
                        old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], old_logo)
                        if os.path.exists(old_logo_path):
                            try:
                                os.remove(old_logo_path)
                            except:
                                pass
                    
                    # Generate unique filename
                    filename = f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.{logo_file.filename.rsplit('.', 1)[1].lower()}"
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'logo', filename)
                    logo_file.save(logo_path)
                    app.config['SCHOOL_LOGO'] = f"logo/{filename}"
        
        # Handle login background image upload
        if 'login_background_image' in request.files:
            bg_file = request.files['login_background_image']
            if bg_file and bg_file.filename:
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in bg_file.filename and bg_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Delete old background if exists
                    old_bg = app.config.get('LOGIN_BACKGROUND_IMAGE', '')
                    if old_bg:
                        old_bg_path = os.path.join(app.config['UPLOAD_FOLDER'], old_bg)
                        if os.path.exists(old_bg_path):
                            try:
                                os.remove(old_bg_path)
                            except:
                                pass
                    
                    # Generate unique filename
                    filename = f"login_bg_{datetime.now().strftime('%Y%m%d%H%M%S')}.{bg_file.filename.rsplit('.', 1)[1].lower()}"
                    bg_path = os.path.join(app.config['UPLOAD_FOLDER'], 'login', filename)
                    os.makedirs(os.path.dirname(bg_path), exist_ok=True)
                    bg_file.save(bg_path)
                    app.config['LOGIN_BACKGROUND_IMAGE'] = f"login/{filename}"
        
        # Landing Page Settings
        app.config['LANDING_PAGE_TITLE'] = request.form.get('landing_page_title', app.config.get('LANDING_PAGE_TITLE', 'Wajina Suite - School Management System'))
        app.config['LANDING_HERO_TITLE'] = request.form.get('landing_hero_title', app.config.get('LANDING_HERO_TITLE', 'Wajina International School'))
        app.config['LANDING_HERO_SUBTITLE'] = request.form.get('landing_hero_subtitle', app.config.get('LANDING_HERO_SUBTITLE', 'Comprehensive School Management System'))
        app.config['LANDING_SHOW_LOGO'] = 'landing_show_logo' in request.form
        app.config['LANDING_SHOW_HERO_BUTTON'] = 'landing_show_hero_button' in request.form
        app.config['LANDING_HERO_BUTTON_TEXT'] = request.form.get('landing_hero_button_text', app.config.get('LANDING_HERO_BUTTON_TEXT', 'Apply for Admission Online'))
        app.config['LANDING_SHOW_FEATURES'] = 'landing_show_features' in request.form
        app.config['LANDING_SHOW_PORTALS'] = 'landing_show_portals' in request.form
        app.config['LANDING_BACKGROUND_COLOR'] = request.form.get('landing_background_color', app.config.get('LANDING_BACKGROUND_COLOR', '#9ACD32'))
        
        # Handle landing page background image upload
        if 'landing_background_image' in request.files:
            landing_bg_file = request.files['landing_background_image']
            if landing_bg_file and landing_bg_file.filename:
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in landing_bg_file.filename and landing_bg_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Delete old background if exists
                    old_landing_bg = app.config.get('LANDING_BACKGROUND_IMAGE', '')
                    if old_landing_bg:
                        old_landing_bg_path = os.path.join(app.config['UPLOAD_FOLDER'], old_landing_bg)
                        if os.path.exists(old_landing_bg_path):
                            try:
                                os.remove(old_landing_bg_path)
                            except:
                                pass
                    
                    # Generate unique filename
                    filename = f"landing_bg_{datetime.now().strftime('%Y%m%d%H%M%S')}.{landing_bg_file.filename.rsplit('.', 1)[1].lower()}"
                    landing_bg_path = os.path.join(app.config['UPLOAD_FOLDER'], 'login', filename)
                    os.makedirs(os.path.dirname(landing_bg_path), exist_ok=True)
                    landing_bg_file.save(landing_bg_path)
                    app.config['LANDING_BACKGROUND_IMAGE'] = f"login/{filename}"
        
        # ID Card Settings
        app.config['ID_CARD_WIDTH'] = int(request.form.get('id_card_width', 500))
        app.config['ID_CARD_HEIGHT'] = int(request.form.get('id_card_height', 0))
        app.config['ID_CARD_BORDER_RADIUS'] = int(request.form.get('id_card_border_radius', 15))
        app.config['ID_CARD_BG_COLOR'] = request.form.get('id_card_bg_color', '#ffffff')
        app.config['ID_CARD_HEADER_BG_COLOR'] = request.form.get('id_card_header_bg_color', '#32CD32')
        app.config['ID_CARD_FOOTER_BG_COLOR'] = request.form.get('id_card_footer_bg_color', '#f8f9fa')
        app.config['ID_CARD_BORDER_COLOR'] = request.form.get('id_card_border_color', '#32CD32')
        app.config['ID_CARD_BORDER_WIDTH'] = int(request.form.get('id_card_border_width', 3))
        app.config['ID_CARD_LOGO_POSITION'] = request.form.get('id_card_logo_position', 'top-center')
        app.config['ID_CARD_LOGO_HEIGHT'] = int(request.form.get('id_card_logo_height', 60))
        app.config['ID_CARD_LOGO_MARGIN_BOTTOM'] = int(request.form.get('id_card_logo_margin_bottom', 10))
        app.config['ID_CARD_PHOTO_POSITION'] = request.form.get('id_card_photo_position', 'left')
        app.config['ID_CARD_PHOTO_WIDTH'] = int(request.form.get('id_card_photo_width', 150))
        app.config['ID_CARD_PHOTO_HEIGHT'] = int(request.form.get('id_card_photo_height', 180))
        app.config['ID_CARD_PHOTO_BORDER_COLOR'] = request.form.get('id_card_photo_border_color', '#32CD32')
        app.config['ID_CARD_PHOTO_BORDER_WIDTH'] = int(request.form.get('id_card_photo_border_width', 3))
        app.config['ID_CARD_TEXT_POSITION'] = request.form.get('id_card_text_position', 'right')
        app.config['ID_CARD_NAME_FONT_SIZE'] = int(request.form.get('id_card_name_font_size', 18))
        app.config['ID_CARD_LABEL_FONT_SIZE'] = int(request.form.get('id_card_label_font_size', 14))
        app.config['ID_CARD_VALUE_FONT_SIZE'] = int(request.form.get('id_card_value_font_size', 16))
        app.config['ID_CARD_TEXT_COLOR'] = request.form.get('id_card_text_color', '#000000')
        app.config['ID_CARD_LABEL_COLOR'] = request.form.get('id_card_label_color', '#666666')
        app.config['ID_CARD_QR_POSITION'] = request.form.get('id_card_qr_position', 'bottom-center')
        app.config['ID_CARD_QR_SIZE'] = int(request.form.get('id_card_qr_size', 120))
        app.config['ID_CARD_SHOW_QR'] = 'id_card_show_qr' in request.form
        app.config['ID_CARD_HEADER_TITLE_SIZE'] = int(request.form.get('id_card_header_title_size', 21))
        app.config['ID_CARD_HEADER_SUBTITLE_SIZE'] = int(request.form.get('id_card_header_subtitle_size', 14))
        app.config['ID_CARD_HEADER_TEXT_COLOR'] = request.form.get('id_card_header_text_color', '#ffffff')
        app.config['ID_CARD_FOOTER_TEXT_COLOR'] = request.form.get('id_card_footer_text_color', '#666666')
        app.config['ID_CARD_FOOTER_FONT_SIZE'] = int(request.form.get('id_card_footer_font_size', 12))
        
        # Persist all settings to file
        save_settings_to_file()
        
        # Reinitialize mail with new settings
        mail.init_app(app)
        
        flash('Settings updated successfully!', 'success')
        # Reload settings to ensure they're in memory
        load_settings_from_file()
        return redirect(url_for('settings'))
    except Exception as e:
        import traceback
        print(f"Error updating settings: {str(e)}")
        traceback.print_exc()
        flash(f'Error updating settings: {str(e)}', 'danger')
        return redirect(url_for('settings'))


# Email Report Routes
@app.route('/reports/<report_type>/send-email', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'store_keeper')
def send_report_email(report_type):
    """Send report via email in PDF and CSV formats"""
    try:
        recipient_email = request.form.get('recipient_email')
        if not recipient_email:
            flash('Recipient email is required!', 'danger')
            return redirect(request.referrer or url_for('reports'))
        
        # Check if email is enabled
        if not app.config.get('ENABLE_EMAIL', True):
            flash('Email notifications are disabled. Please enable them in settings.', 'danger')
            return redirect(request.referrer or url_for('reports'))
        
        # Check if email is configured
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            flash('Email is not configured. Please configure email settings first.', 'danger')
            return redirect(url_for('settings'))
        
        # Get report data based on type
        pdf_buffer = None
        csv_buffer = None
        report_name = ''
        filters = {}
        
        if report_type == 'learners':
            # Get filters from request
            search = request.form.get('search', '')
            class_filter = request.form.get('class', '')
            status_filter = request.form.get('status', 'active')
            
            query = Learner.query.join(User).filter(User.is_active == True)
            if search:
                query = query.filter(
                    db.or_(
                        Learner.admission_number.ilike(f'%{search}%'),
                        User.first_name.ilike(f'%{search}%'),
                        User.last_name.ilike(f'%{search}%')
                    )
                )
            if class_filter:
                query = query.filter(Learner.current_class == class_filter)
            if status_filter:
                query = query.filter(Learner.status == status_filter)
            
            learners = query.all()
            filters = {'class': class_filter, 'status': status_filter}
            pdf_buffer = generate_learner_pdf(learners, filters, school_info)
            csv_buffer = generate_learner_csv(learners, filters)
            report_name = 'Learner Report'
            
        elif report_type == 'attendance':
            class_filter = request.form.get('class', '')
            start_date = request.form.get('start_date', '')
            end_date = request.form.get('end_date', '')
            
            if not start_date:
                start_date = date.today().replace(day=1).isoformat()
            if not end_date:
                end_date = date.today().isoformat()
            
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                start = date.today().replace(day=1)
                end = date.today()
            
            # Get attendance data
            base_query = db.session.query(Learner).join(User, Learner.user_id == User.id)
            if class_filter:
                base_query = base_query.filter(Learner.current_class == class_filter)
            learners_list = base_query.filter(Learner.status == 'active').all()
            
            attendance_data = []
            for learner in learners_list:
                present_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='present'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                absent_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='absent'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                late_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='late'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                
                attendance_data.append({
                    'id': learner.id,
                    'admission_number': learner.admission_number,
                    'first_name': learner.user.first_name,
                    'last_name': learner.user.last_name,
                    'current_class': learner.current_class,
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days
                })
            
            total_days = (end - start).days + 1
            present_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'present'
            ).count()
            absent_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'absent'
            ).count()
            late_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'late'
            ).count()
            
            filters = {
                'start_date': start_date,
                'end_date': end_date,
                'class': class_filter,
                'total_days': total_days,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count
            }
            
            pdf_buffer = generate_attendance_pdf(attendance_data, filters, school_info)
            csv_buffer = generate_attendance_csv(attendance_data, filters)
            report_name = 'Attendance Report'
            
        elif report_type == 'fees':
            status_filter = request.form.get('status', '')
            fee_type_filter = request.form.get('fee_type', '')
            session_filter = request.form.get('session', '')
            term_filter = request.form.get('term', '')
            
            query = Fee.query
            if status_filter:
                query = query.filter_by(status=status_filter)
            if fee_type_filter:
                query = query.filter_by(fee_type=fee_type_filter)
            if session_filter:
                query = query.filter_by(session=session_filter)
            if term_filter:
                query = query.filter_by(term=term_filter)
            
            fees = query.all()
            
            total_amount = db.session.query(db.func.sum(Fee.amount)).scalar() or 0
            paid_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
            pending_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
            
            filters = {
                'status': status_filter,
                'fee_type': fee_type_filter,
                'total_amount': float(total_amount),
                'paid_amount': float(paid_amount),
                'pending_amount': float(pending_amount)
            }
            
            pdf_buffer = generate_fee_pdf(fees, filters, school_info)
            csv_buffer = generate_fee_csv(fees, filters)
            report_name = 'Fee Report'
            
        elif report_type == 'store':
            search = request.form.get('search', '')
            category = request.form.get('category', '')
            status = request.form.get('status', '')
            
            query = StoreItem.query
            if search:
                query = query.filter(
                    db.or_(
                        StoreItem.item_code.ilike(f'%{search}%'),
                        StoreItem.item_name.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            
            items = query.order_by(StoreItem.item_name).all()
            
            total_items = len(items)
            total_value = sum([float(item.total_value) for item in items])
            low_stock_items = len([item for item in items if item.is_low_stock])
            out_of_stock = len([item for item in items if item.status == 'out_of_stock'])
            
            filters = {
                'category': category,
                'status': status,
                'total_items': total_items,
                'total_value': total_value,
                'low_stock_items': low_stock_items,
                'out_of_stock': out_of_stock
            }
            
            pdf_buffer = generate_store_pdf(items, filters, school_info)
            csv_buffer = generate_store_csv(items, filters)
            report_name = 'Store Inventory Report'
            
        elif report_type == 'expenditures':
            search = request.form.get('search', '')
            category = request.form.get('category', '')
            status = request.form.get('status', '')
            staff_id = request.form.get('staff_id', '')
            start_date = request.form.get('start_date', '')
            end_date = request.form.get('end_date', '')
            
            query = Expenditure.query
            if search:
                query = query.filter(
                    db.or_(
                        Expenditure.expense_code.ilike(f'%{search}%'),
                        Expenditure.title.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            if staff_id:
                query = query.filter(
                    db.or_(
                        Expenditure.approved_by == int(staff_id),
                        Expenditure.created_by == int(staff_id)
                    )
                )
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date >= start)
                except:
                    pass
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date <= end)
                except:
                    pass
            
            expenditures = query.order_by(Expenditure.payment_date.desc()).all()
            
            total_amount = sum([float(exp.amount) for exp in expenditures])
            paid_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'paid'])
            pending_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'pending'])
            
            filters = {
                'category': category,
                'status': status,
                'start_date': start_date,
                'end_date': end_date,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': pending_amount
            }
            
            pdf_buffer = generate_expenditure_pdf(expenditures, filters, school_info)
            csv_buffer = generate_expenditure_csv(expenditures, filters)
            report_name = 'Expenditure Report'
        else:
            flash('Invalid report type!', 'danger')
            return redirect(request.referrer or url_for('reports'))
        
        # Create email message
        school_name = app.config.get('SCHOOL_NAME', 'Wajina International School')
        msg = Message(
            subject=f'{school_name} - {report_name}',
            recipients=[recipient_email],
            sender=app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
        )
        
        # Email body
        msg.body = f"""
Dear Recipient,

Please find attached the {report_name} from {school_name}.

Report generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}

This email contains:
- PDF version of the report
- CSV version of the report for data analysis

Best regards,
{school_name} Administration
"""
        
        # Attach PDF
        pdf_buffer.seek(0)
        msg.attach(
            filename=f'{report_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf',
            content_type='application/pdf',
            data=pdf_buffer.read()
        )
        
        # Attach CSV
        csv_buffer.seek(0)
        msg.attach(
            filename=f'{report_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv',
            content_type='text/csv',
            data=csv_buffer.read()
        )
        
        # Send email
        mail.send(msg)
        
        flash(f'Report sent successfully to {recipient_email}!', 'success')
        return redirect(request.referrer or url_for('reports'))
        
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('reports'))


# Download Report Routes
@app.route('/reports/<report_type>/download-pdf')
@login_required
@role_required('admin', 'teacher', 'store_keeper')
def download_report_pdf(report_type):
    """Download report as PDF"""
    try:
        if report_type == 'learners':
            search = request.args.get('search', '')
            class_filter = request.args.get('class', '')
            status_filter = request.args.get('status', 'active')
            
            query = Learner.query.join(User).filter(User.is_active == True)
            if search:
                query = query.filter(
                    db.or_(
                        Learner.admission_number.ilike(f'%{search}%'),
                        User.first_name.ilike(f'%{search}%'),
                        User.last_name.ilike(f'%{search}%')
                    )
                )
            if class_filter:
                query = query.filter(Learner.current_class == class_filter)
            if status_filter:
                query = query.filter(Learner.status == status_filter)
            
            learners = query.all()
            filters = {'class': class_filter, 'status': status_filter}
            pdf_buffer = generate_learner_pdf(learners, filters)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'learner_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        elif report_type == 'attendance':
            class_filter = request.args.get('class', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            if not start_date:
                start_date = date.today().replace(day=1).isoformat()
            if not end_date:
                end_date = date.today().isoformat()
            
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                start = date.today().replace(day=1)
                end = date.today()
            
            base_query = db.session.query(Learner).join(User, Learner.user_id == User.id)
            if class_filter:
                base_query = base_query.filter(Learner.current_class == class_filter)
            learners_list = base_query.filter(Learner.status == 'active').all()
            
            attendance_data = []
            for learner in learners_list:
                present_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='present'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                absent_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='absent'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                late_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='late'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                
                attendance_data.append({
                    'id': learner.id,
                    'admission_number': learner.admission_number,
                    'first_name': learner.user.first_name,
                    'last_name': learner.user.last_name,
                    'current_class': learner.current_class,
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days
                })
            
            total_days = (end - start).days + 1
            present_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'present'
            ).count()
            absent_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'absent'
            ).count()
            late_count = Attendance.query.filter(
                Attendance.date >= start, Attendance.date <= end, Attendance.status == 'late'
            ).count()
            
            filters = {
                'start_date': start_date,
                'end_date': end_date,
                'class': class_filter,
                'total_days': total_days,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count
            }
            
            pdf_buffer = generate_attendance_pdf(attendance_data, filters)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'attendance_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        elif report_type == 'fees':
            status_filter = request.args.get('status', '')
            fee_type_filter = request.args.get('fee_type', '')
            session_filter = request.args.get('session', '')
            term_filter = request.args.get('term', '')
            
            query = Fee.query
            if status_filter:
                query = query.filter_by(status=status_filter)
            if fee_type_filter:
                query = query.filter_by(fee_type=fee_type_filter)
            if session_filter:
                query = query.filter_by(session=session_filter)
            if term_filter:
                query = query.filter_by(term=term_filter)
            
            fees = query.all()
            
            total_amount = db.session.query(db.func.sum(Fee.amount)).scalar() or 0
            paid_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
            pending_amount = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
            
            filters = {
                'status': status_filter,
                'fee_type': fee_type_filter,
                'total_amount': float(total_amount),
                'paid_amount': float(paid_amount),
                'pending_amount': float(pending_amount)
            }
            
            pdf_buffer = generate_fee_pdf(fees, filters)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'fee_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        elif report_type == 'store':
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            
            query = StoreItem.query
            if search:
                query = query.filter(
                    db.or_(
                        StoreItem.item_code.ilike(f'%{search}%'),
                        StoreItem.item_name.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            
            items = query.order_by(StoreItem.item_name).all()
            
            total_items = len(items)
            total_value = sum([float(item.total_value) for item in items])
            low_stock_items = len([item for item in items if item.is_low_stock])
            out_of_stock = len([item for item in items if item.status == 'out_of_stock'])
            
            filters = {
                'category': category,
                'status': status,
                'total_items': total_items,
                'total_value': total_value,
                'low_stock_items': low_stock_items,
                'out_of_stock': out_of_stock
            }
            
            pdf_buffer = generate_store_pdf(items, filters)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'store_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        elif report_type == 'expenditures':
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            staff_id = request.args.get('staff_id', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            query = Expenditure.query
            if search:
                query = query.filter(
                    db.or_(
                        Expenditure.expense_code.ilike(f'%{search}%'),
                        Expenditure.title.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            if staff_id:
                query = query.filter(
                    db.or_(
                        Expenditure.approved_by == int(staff_id),
                        Expenditure.created_by == int(staff_id)
                    )
                )
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date >= start)
                except:
                    pass
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date <= end)
                except:
                    pass
            
            expenditures = query.order_by(Expenditure.payment_date.desc()).all()
            
            total_amount = sum([float(exp.amount) for exp in expenditures])
            paid_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'paid'])
            pending_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'pending'])
            
            filters = {
                'category': category,
                'status': status,
                'start_date': start_date,
                'end_date': end_date,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': pending_amount
            }
            
            pdf_buffer = generate_expenditure_pdf(expenditures, filters)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'expenditure_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
        else:
            flash('Invalid report type!', 'danger')
            return redirect(url_for('reports'))
            
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('reports'))


@app.route('/reports/<report_type>/download-csv')
@login_required
@role_required('admin', 'teacher', 'store_keeper')
def download_report_csv(report_type):
    """Download report as CSV"""
    try:
        if report_type == 'learners':
            search = request.args.get('search', '')
            class_filter = request.args.get('class', '')
            status_filter = request.args.get('status', 'active')
            
            query = Learner.query.join(User).filter(User.is_active == True)
            if search:
                query = query.filter(
                    db.or_(
                        Learner.admission_number.ilike(f'%{search}%'),
                        User.first_name.ilike(f'%{search}%'),
                        User.last_name.ilike(f'%{search}%')
                    )
                )
            if class_filter:
                query = query.filter(Learner.current_class == class_filter)
            if status_filter:
                query = query.filter(Learner.status == status_filter)
            
            learners = query.all()
            csv_buffer = generate_learner_csv(learners)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=learner_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
            
        elif report_type == 'attendance':
            class_filter = request.args.get('class', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            if not start_date:
                start_date = date.today().replace(day=1).isoformat()
            if not end_date:
                end_date = date.today().isoformat()
            
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                start = date.today().replace(day=1)
                end = date.today()
            
            base_query = db.session.query(Learner).join(User, Learner.user_id == User.id)
            if class_filter:
                base_query = base_query.filter(Learner.current_class == class_filter)
            learners_list = base_query.filter(Learner.status == 'active').all()
            
            attendance_data = []
            for learner in learners_list:
                present_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='present'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                absent_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='absent'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                late_days = Attendance.query.filter_by(
                    learner_id=learner.id, status='late'
                ).filter(Attendance.date >= start, Attendance.date <= end).count()
                
                attendance_data.append({
                    'id': learner.id,
                    'admission_number': learner.admission_number,
                    'first_name': learner.user.first_name,
                    'last_name': learner.user.last_name,
                    'current_class': learner.current_class,
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days
                })
            
            csv_buffer = generate_attendance_csv(attendance_data)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=attendance_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
            
        elif report_type == 'fees':
            status_filter = request.args.get('status', '')
            fee_type_filter = request.args.get('fee_type', '')
            session_filter = request.args.get('session', '')
            term_filter = request.args.get('term', '')
            
            query = Fee.query
            if status_filter:
                query = query.filter_by(status=status_filter)
            if fee_type_filter:
                query = query.filter_by(fee_type=fee_type_filter)
            if session_filter:
                query = query.filter_by(session=session_filter)
            if term_filter:
                query = query.filter_by(term=term_filter)
            
            fees = query.all()
            csv_buffer = generate_fee_csv(fees)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=fee_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
            
        elif report_type == 'store':
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            
            query = StoreItem.query
            if search:
                query = query.filter(
                    db.or_(
                        StoreItem.item_code.ilike(f'%{search}%'),
                        StoreItem.item_name.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            
            items = query.order_by(StoreItem.item_name).all()
            csv_buffer = generate_store_csv(items)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=store_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
            
        elif report_type == 'expenditures':
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            staff_id = request.args.get('staff_id', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            query = Expenditure.query
            if search:
                query = query.filter(
                    db.or_(
                        Expenditure.expense_code.ilike(f'%{search}%'),
                        Expenditure.title.ilike(f'%{search}%')
                    )
                )
            if category:
                query = query.filter_by(category=category)
            if status:
                query = query.filter_by(status=status)
            if staff_id:
                query = query.filter(
                    db.or_(
                        Expenditure.approved_by == int(staff_id),
                        Expenditure.created_by == int(staff_id)
                    )
                )
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date >= start)
                except:
                    pass
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Expenditure.payment_date <= end)
                except:
                    pass
            
            expenditures = query.order_by(Expenditure.payment_date.desc()).all()
            csv_buffer = generate_expenditure_csv(expenditures)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=expenditure_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        
        elif report_type == 'parents':
            search = request.args.get('search', '')
            
            # Get unique parents with their children count
            query = db.session.query(
                Learner.parent_name,
                Learner.parent_phone,
                Learner.parent_email,
                Learner.parent_address,
                db.func.count(Learner.id).label('children_count')
            ).filter(
                Learner.status == 'active',
                Learner.parent_name.isnot(None),
                Learner.parent_name != ''
            )
            
            if search:
                query = query.filter(
                    db.or_(
                        Learner.parent_name.ilike(f'%{search}%'),
                        Learner.parent_phone.ilike(f'%{search}%'),
                        Learner.parent_email.ilike(f'%{search}%')
                    )
                )
            
            query = query.group_by(
                Learner.parent_name,
                Learner.parent_phone,
                Learner.parent_email,
                Learner.parent_address
            )
            
            parent_groups = query.all()
            
            # Get all parents with their children details
            parents_data = []
            for parent_group in parent_groups:
                learners = Learner.query.filter(
                    Learner.status == 'active',
                    Learner.parent_name == parent_group.parent_name,
                    Learner.parent_phone == parent_group.parent_phone
                ).all()
                
                children_names = ', '.join([f"{l.user.first_name} {l.user.last_name} ({l.admission_number})" for l in learners])
                
                parents_data.append({
                    'parent_name': parent_group.parent_name,
                    'parent_phone': parent_group.parent_phone or 'N/A',
                    'parent_email': parent_group.parent_email or 'N/A',
                    'parent_address': parent_group.parent_address or 'N/A',
                    'children_count': parent_group.children_count,
                    'children_names': children_names
                })
            
            # Sort by children count
            parents_data.sort(key=lambda x: x['children_count'], reverse=True)
            
            # Generate CSV
            buffer = BytesIO()
            writer = csv.writer(buffer)
            
            # Header
            writer.writerow(['Parent/Guardian Name', 'Phone', 'Email', 'Address', 'Number of Children', 'Children (Name - Admission Number)'])
            
            # Data rows
            for parent in parents_data:
                writer.writerow([
                    parent['parent_name'],
                    parent['parent_phone'],
                    parent['parent_email'],
                    parent['parent_address'],
                    parent['children_count'],
                    parent['children_names']
                ])
            
            buffer.seek(0)
            return Response(
                buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=parent_guardian_report_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        
        else:
            flash('Invalid report type!', 'danger')
            return redirect(url_for('reports'))
            
    except Exception as e:
        flash(f'Error generating CSV: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('reports'))


# Store Management Routes
@app.route('/store')
@login_required
@role_required('admin', 'store_keeper')
def store_list():
    """List all store items"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = StoreItem.query
    
    if search:
        query = query.filter(
            db.or_(
                StoreItem.item_code.ilike(f'%{search}%'),
                StoreItem.item_name.ilike(f'%{search}%'),
                StoreItem.description.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    
    items = query.order_by(StoreItem.item_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(StoreItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Statistics
    total_items = StoreItem.query.count()
    low_stock_items = StoreItem.query.filter(
        db.cast(StoreItem.quantity, db.Float) <= db.cast(StoreItem.min_quantity, db.Float)
    ).count()
    out_of_stock = StoreItem.query.filter_by(status='out_of_stock').count()
    total_value = db.session.query(db.func.sum(StoreItem.quantity * StoreItem.unit_price)).scalar() or 0
    
    stats = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock': out_of_stock,
        'total_value': float(total_value)
    }
    
    return render_template('store/list.html', items=items, search=search, 
                          category=category, status=status, categories=categories, stats=stats)


@app.route('/store/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'store_keeper')
def add_store_item():
    """Add new store item"""
    if request.method == 'POST':
        try:
            item = StoreItem(
                item_code=request.form.get('item_code'),
                item_name=request.form.get('item_name'),
                category=request.form.get('category'),
                description=request.form.get('description', ''),
                unit=request.form.get('unit'),
                quantity=float(request.form.get('quantity', 0) or 0),
                min_quantity=float(request.form.get('min_quantity', 0) or 0),
                unit_price=float(request.form.get('unit_price', 0) or 0),
                supplier=request.form.get('supplier', ''),
                supplier_contact=request.form.get('supplier_contact', ''),
                location=request.form.get('location', ''),
                purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date() if request.form.get('purchase_date') else None,
                expiry_date=datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date() if request.form.get('expiry_date') else None,
                notes=request.form.get('notes', ''),
                created_by=current_user.id,
                status='active'
            )
            
            # Check if low stock
            if item.quantity <= item.min_quantity:
                item.status = 'low_stock' if item.quantity > 0 else 'out_of_stock'
            
            db.session.add(item)
            db.session.commit()
            
            flash('Store item added successfully!', 'success')
            return redirect(url_for('store_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding store item: {str(e)}', 'danger')
    
    # Get existing categories for suggestions
    categories = db.session.query(StoreItem.category).distinct().all()
    existing_categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('store/add.html', existing_categories=existing_categories)


@app.route('/store/<int:item_id>')
@login_required
@role_required('admin', 'store_keeper')
def view_store_item(item_id):
    """View store item details"""
    item = StoreItem.query.get_or_404(item_id)
    transactions = StoreTransaction.query.filter_by(item_id=item_id).order_by(
        StoreTransaction.transaction_date.desc(), StoreTransaction.created_at.desc()
    ).limit(50).all()
    
    from datetime import date as date_class
    return render_template('store/view.html', item=item, transactions=transactions, date=date_class)


@app.route('/store/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'store_keeper')
def edit_store_item(item_id):
    """Edit store item"""
    item = StoreItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        try:
            item.item_code = request.form.get('item_code')
            item.item_name = request.form.get('item_name')
            item.category = request.form.get('category')
            item.description = request.form.get('description', '')
            item.unit = request.form.get('unit')
            item.quantity = float(request.form.get('quantity', 0) or 0)
            item.min_quantity = float(request.form.get('min_quantity', 0) or 0)
            item.unit_price = float(request.form.get('unit_price', 0) or 0)
            item.supplier = request.form.get('supplier', '')
            item.supplier_contact = request.form.get('supplier_contact', '')
            item.location = request.form.get('location', '')
            item.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date() if request.form.get('purchase_date') else None
            item.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date() if request.form.get('expiry_date') else None
            item.notes = request.form.get('notes', '')
            item.updated_at = datetime.utcnow()
            
            # Update status based on quantity
            if item.quantity <= 0:
                item.status = 'out_of_stock'
            elif item.quantity <= item.min_quantity:
                item.status = 'low_stock'
            else:
                item.status = 'active'
            
            db.session.commit()
            flash('Store item updated successfully!', 'success')
            return redirect(url_for('view_store_item', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating store item: {str(e)}', 'danger')
    
    # Get existing categories for suggestions
    categories = db.session.query(StoreItem.category).distinct().all()
    existing_categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('store/edit.html', item=item, existing_categories=existing_categories)


@app.route('/store/<int:item_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'store_keeper')
def delete_store_item(item_id):
    """Delete store item"""
    item = StoreItem.query.get_or_404(item_id)
    
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Store item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting store item: {str(e)}', 'danger')
    
    return redirect(url_for('store_list'))


@app.route('/store/<int:item_id>/transaction', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'store_keeper')
def add_store_transaction(item_id):
    """Add transaction for store item"""
    item = StoreItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        try:
            transaction_type = request.form.get('transaction_type')
            quantity = float(request.form.get('quantity', 0) or 0)
            unit_price = float(request.form.get('unit_price', 0) or item.unit_price or 0)
            
            if quantity <= 0:
                flash('Quantity must be greater than 0!', 'danger')
                return redirect(url_for('add_store_transaction', item_id=item_id))
            
            # Create transaction
            transaction = StoreTransaction(
                item_id=item_id,
                transaction_type=transaction_type,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=quantity * unit_price,
                reference_number=request.form.get('reference_number', ''),
                supplier=request.form.get('supplier', ''),
                recipient=request.form.get('recipient', ''),
                purpose=request.form.get('purpose', ''),
                notes=request.form.get('notes', ''),
                transaction_date=datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d').date() if request.form.get('transaction_date') else date.today(),
                created_by=current_user.id
            )
            
            # Update item quantity
            if transaction_type == 'in':
                item.quantity += quantity
            elif transaction_type == 'out':
                if item.quantity < quantity:
                    flash(f'Insufficient stock! Available: {item.quantity}', 'danger')
                    return redirect(url_for('add_store_transaction', item_id=item_id))
                item.quantity -= quantity
            elif transaction_type == 'adjustment':
                item.quantity = quantity  # Set to new quantity
            elif transaction_type == 'return':
                item.quantity += quantity
            
            # Update item status
            if item.quantity <= 0:
                item.status = 'out_of_stock'
            elif item.quantity <= item.min_quantity:
                item.status = 'low_stock'
            else:
                item.status = 'active'
            
            # Update unit price if provided
            if unit_price > 0:
                item.unit_price = unit_price
            
            db.session.add(transaction)
            item.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Transaction recorded successfully!', 'success')
            return redirect(url_for('view_store_item', item_id=item_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording transaction: {str(e)}', 'danger')
    
    return render_template('store/transaction.html', item=item)


@app.route('/store/transactions')
@login_required
@role_required('admin', 'store_keeper')
def store_transactions():
    """View all store transactions"""
    search = request.args.get('search', '')
    transaction_type = request.args.get('transaction_type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    
    query = StoreTransaction.query.join(StoreItem)
    
    if search:
        query = query.filter(
            db.or_(
                StoreItem.item_code.ilike(f'%{search}%'),
                StoreItem.item_name.ilike(f'%{search}%'),
                StoreTransaction.reference_number.ilike(f'%{search}%')
            )
        )
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(StoreTransaction.transaction_date >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(StoreTransaction.transaction_date <= end)
        except:
            pass
    
    transactions = query.order_by(
        StoreTransaction.transaction_date.desc(), StoreTransaction.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('store/transactions.html', transactions=transactions,
                          search=search, transaction_type=transaction_type,
                          start_date=start_date, end_date=end_date)


# Store Reports Routes
@app.route('/reports/store')
@login_required
@role_required('admin', 'store_keeper')
def store_reports():
    """Store inventory reports"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    query = StoreItem.query
    
    if search:
        query = query.filter(
            db.or_(
                StoreItem.item_code.ilike(f'%{search}%'),
                StoreItem.item_name.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    
    items = query.order_by(StoreItem.item_name).all()
    
    # Get categories for filter
    categories = db.session.query(StoreItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Statistics
    total_items = len(items)
    total_value = sum([float(item.total_value) for item in items])
    low_stock_items = len([item for item in items if item.is_low_stock])
    out_of_stock = len([item for item in items if item.status == 'out_of_stock'])
    
    stats = {
        'total_items': total_items,
        'total_value': total_value,
        'low_stock_items': low_stock_items,
        'out_of_stock': out_of_stock
    }
    
    filters = {
        'category': category,
        'status': status,
        'total_items': total_items,
        'total_value': total_value,
        'low_stock_items': low_stock_items,
        'out_of_stock': out_of_stock
    }
    
    return render_template('reports/store.html', items=items, search=search,
                          category=category, status=status, categories=categories, stats=stats, filters=filters, settings=get_school_settings())


# Expenditure Reports Routes
@app.route('/reports/expenditures')
@login_required
@role_required('admin', 'store_keeper')
def expenditure_reports():
    """Expenditure reports"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    staff_id = request.args.get('staff_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Expenditure.query
    
    if search:
        query = query.filter(
            db.or_(
                Expenditure.expense_code.ilike(f'%{search}%'),
                Expenditure.title.ilike(f'%{search}%'),
                Expenditure.vendor.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if staff_id:
        query = query.filter(
            db.or_(
                Expenditure.approved_by == int(staff_id),
                Expenditure.created_by == int(staff_id)
            )
        )
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expenditure.payment_date >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expenditure.payment_date <= end)
        except:
            pass
    
    expenditures = query.order_by(Expenditure.payment_date.desc()).all()
    
    # Get categories for filter
    categories = db.session.query(Expenditure.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Get staff for filter
    staff_members = Staff.query.join(User).filter(User.is_active == True).all()
    
    # Statistics
    total_amount = sum([float(exp.amount) for exp in expenditures])
    paid_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'paid'])
    pending_amount = sum([float(exp.amount) for exp in expenditures if exp.status == 'pending'])
    
    stats = {
        'total_expenditures': len(expenditures),
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount
    }
    
    filters = {
        'category': category,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount
    }
    
    return render_template('reports/expenditures.html', expenditures=expenditures, search=search,
                          category=category, status=status, staff_id=staff_id,
                          start_date=start_date, end_date=end_date,
                          categories=categories, staff_members=staff_members, stats=stats, filters=filters, settings=get_school_settings())


# Expenditure Management Routes
@app.route('/expenditures')
@login_required
@role_required('admin', 'store_keeper', 'cashier')
def expenditures_list():
    """List all expenditures"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    staff_id = request.args.get('staff_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    
    query = Expenditure.query
    
    if search:
        query = query.filter(
            db.or_(
                Expenditure.expense_code.ilike(f'%{search}%'),
                Expenditure.title.ilike(f'%{search}%'),
                Expenditure.description.ilike(f'%{search}%'),
                Expenditure.vendor.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if staff_id:
        query = query.filter(
            db.or_(
                Expenditure.approved_by == int(staff_id),
                Expenditure.created_by == int(staff_id)
            )
        )
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expenditure.payment_date >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expenditure.payment_date <= end)
        except:
            pass
    
    expenditures = query.order_by(Expenditure.payment_date.desc(), Expenditure.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(Expenditure.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Get staff for filter
    staff_members = Staff.query.join(User).filter(User.is_active == True).all()
    
    # Statistics
    total_expenditures = Expenditure.query.count()
    total_amount = db.session.query(db.func.sum(Expenditure.amount)).scalar() or 0
    pending_amount = db.session.query(db.func.sum(Expenditure.amount)).filter_by(status='pending').scalar() or 0
    paid_amount = db.session.query(db.func.sum(Expenditure.amount)).filter_by(status='paid').scalar() or 0
    
    stats = {
        'total_expenditures': total_expenditures,
        'total_amount': float(total_amount),
        'pending_amount': float(pending_amount),
        'paid_amount': float(paid_amount)
    }
    
    return render_template('expenditures/list.html', expenditures=expenditures, search=search,
                          category=category, status=status, staff_id=staff_id,
                          start_date=start_date, end_date=end_date,
                          categories=categories, staff_members=staff_members, stats=stats)


@app.route('/expenditures/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'store_keeper', 'cashier')
def add_expenditure():
    """Add new expenditure"""
    if request.method == 'POST':
        try:
            # Generate expense code if not provided
            expense_code = request.form.get('expense_code', '').strip()
            if not expense_code:
                # Auto-generate code
                title = request.form.get('title', '')
                words = title.split(' ')[:2] if title else ['EXP']
                code = ''.join([w[:3].upper() for w in words if w]) + '-' + datetime.now().strftime('%Y%m%d%H%M%S')[-6:]
                expense_code = code
            
            # Handle receipt file upload
            receipt_file_path = None
            if 'receipt_file' in request.files:
                receipt_file = request.files['receipt_file']
                if receipt_file and receipt_file.filename:
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
                    file_ext = receipt_file.filename.rsplit('.', 1)[1].lower() if '.' in receipt_file.filename else ''
                    if file_ext in allowed_extensions:
                        # Generate unique filename
                        filename = f"receipt_{expense_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                        receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts', filename)
                        receipt_file.save(receipt_path)
                        receipt_file_path = f"receipts/{filename}"
            
            expenditure = Expenditure(
                expense_code=expense_code,
                title=request.form.get('title'),
                description=request.form.get('description', ''),
                category=request.form.get('category'),
                amount=float(request.form.get('amount', 0) or 0),
                payment_method=request.form.get('payment_method', ''),
                payment_date=datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date() if request.form.get('payment_date') else date.today(),
                receipt_number=request.form.get('receipt_number', ''),
                receipt_file=receipt_file_path,
                vendor=request.form.get('vendor', ''),
                vendor_contact=request.form.get('vendor_contact', ''),
                approved_by=int(request.form.get('approved_by')) if request.form.get('approved_by') else None,
                session=request.form.get('session', ''),
                term=request.form.get('term', ''),
                status=request.form.get('status', 'pending'),
                notes=request.form.get('notes', ''),
                created_by=current_user.id
            )
            
            db.session.add(expenditure)
            db.session.commit()
            
            flash('Expenditure added successfully!', 'success')
            return redirect(url_for('expenditures_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding expenditure: {str(e)}', 'danger')
    
    # Get existing categories for suggestions
    categories = db.session.query(Expenditure.category).distinct().all()
    existing_categories = [cat[0] for cat in categories if cat[0]]
    
    # Get staff members for approval dropdown
    staff_members = Staff.query.join(User).filter(User.is_active == True).all()
    
    # Get current session and term from app config
    current_session = app.config.get('CURRENT_SESSION', '')
    current_term = app.config.get('CURRENT_TERM', '')
    today_date = date.today().isoformat()
    
    return render_template('expenditures/add.html', existing_categories=existing_categories,
                          staff_members=staff_members, current_session=current_session, 
                          current_term=current_term, today_date=today_date)


@app.route('/expenditures/<int:expenditure_id>')
@login_required
@role_required('admin', 'store_keeper', 'cashier')
def view_expenditure(expenditure_id):
    """View expenditure details"""
    expenditure = Expenditure.query.get_or_404(expenditure_id)
    
    return render_template('expenditures/view.html', expenditure=expenditure)


@app.route('/expenditures/<int:expenditure_id>/receipt')
@login_required
@role_required('admin', 'store_keeper')
def view_expenditure_receipt(expenditure_id):
    """View/download expenditure receipt"""
    expenditure = Expenditure.query.get_or_404(expenditure_id)
    
    if not expenditure.receipt_file:
        flash('No receipt file available for this expenditure.', 'warning')
        return redirect(url_for('view_expenditure', expenditure_id=expenditure_id))
    
    receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], expenditure.receipt_file)
    
    if not os.path.exists(receipt_path):
        flash('Receipt file not found.', 'danger')
        return redirect(url_for('view_expenditure', expenditure_id=expenditure_id))
    
    return send_file(receipt_path, as_attachment=False)


@app.route('/expenditures/<int:expenditure_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'store_keeper')
def edit_expenditure(expenditure_id):
    """Edit expenditure"""
    expenditure = Expenditure.query.get_or_404(expenditure_id)
    
    if request.method == 'POST':
        try:
            expenditure.title = request.form.get('title')
            expenditure.description = request.form.get('description', '')
            expenditure.category = request.form.get('category')
            expenditure.amount = float(request.form.get('amount', 0) or 0)
            expenditure.payment_method = request.form.get('payment_method', '')
            expenditure.payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date() if request.form.get('payment_date') else date.today()
            expenditure.receipt_number = request.form.get('receipt_number', '')
            expenditure.vendor = request.form.get('vendor', '')
            expenditure.vendor_contact = request.form.get('vendor_contact', '')
            expenditure.approved_by = int(request.form.get('approved_by')) if request.form.get('approved_by') else None
            expenditure.session = request.form.get('session', '')
            expenditure.term = request.form.get('term', '')
            expenditure.status = request.form.get('status', 'pending')
            expenditure.notes = request.form.get('notes', '')
            expenditure.updated_at = datetime.utcnow()
            
            # Handle receipt file upload (only if new file is uploaded)
            if 'receipt_file' in request.files:
                receipt_file = request.files['receipt_file']
                if receipt_file and receipt_file.filename:
                    # Delete old receipt if exists
                    if expenditure.receipt_file:
                        old_receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], expenditure.receipt_file)
                        if os.path.exists(old_receipt_path):
                            try:
                                os.remove(old_receipt_path)
                            except:
                                pass
                    
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
                    file_ext = receipt_file.filename.rsplit('.', 1)[1].lower() if '.' in receipt_file.filename else ''
                    if file_ext in allowed_extensions:
                        # Generate unique filename
                        filename = f"receipt_{expenditure.expense_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                        receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts', filename)
                        receipt_file.save(receipt_path)
                        expenditure.receipt_file = f"receipts/{filename}"
            
            db.session.commit()
            flash('Expenditure updated successfully!', 'success')
            return redirect(url_for('view_expenditure', expenditure_id=expenditure.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating expenditure: {str(e)}', 'danger')
    
    # Get existing categories for suggestions
    categories = db.session.query(Expenditure.category).distinct().all()
    existing_categories = [cat[0] for cat in categories if cat[0]]
    
    # Get staff members for approval dropdown
    staff_members = Staff.query.join(User).filter(User.is_active == True).all()
    
    return render_template('expenditures/edit.html', expenditure=expenditure,
                          existing_categories=existing_categories, staff_members=staff_members)


@app.route('/expenditures/<int:expenditure_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_expenditure(expenditure_id):
    """Delete expenditure (admin only)"""
    expenditure = Expenditure.query.get_or_404(expenditure_id)
    
    try:
        # Delete receipt file if exists
        if expenditure.receipt_file:
            receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], expenditure.receipt_file)
            if os.path.exists(receipt_path):
                try:
                    os.remove(receipt_path)
                except:
                    pass
        
        db.session.delete(expenditure)
        db.session.commit()
        flash('Expenditure deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting expenditure: {str(e)}', 'danger')
    
    return redirect(url_for('expenditures_list'))


# ==================== SALARY MANAGEMENT ROUTES ====================

@app.route('/salaries')
@login_required
@role_required('admin')
def salaries_list():
    """List all staff salaries"""
    page = request.args.get('page', 1, type=int)
    month_filter = request.args.get('month', '')
    year_filter = request.args.get('year', datetime.now().year, type=int)
    status_filter = request.args.get('status', '')
    
    query = Salary.query
    
    if month_filter:
        query = query.filter(Salary.month == month_filter)
    if year_filter:
        query = query.filter(Salary.year == year_filter)
    if status_filter:
        query = query.filter(Salary.status == status_filter)
    
    salaries = query.order_by(Salary.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics
    total_paid = db.session.query(db.func.sum(Salary.net_salary)).filter(
        Salary.status == 'paid',
        Salary.year == year_filter
    ).scalar() or 0
    
    total_pending = db.session.query(db.func.sum(Salary.net_salary)).filter(
        Salary.status == 'pending',
        Salary.year == year_filter
    ).scalar() or 0
    
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    return render_template('salaries/list.html',
                         salaries=salaries,
                         months=months,
                         month_filter=month_filter,
                         year_filter=year_filter,
                         status_filter=status_filter,
                         total_paid=float(total_paid),
                         total_pending=float(total_pending))


@app.route('/salaries/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_salary():
    """Add new salary record"""
    if request.method == 'POST':
        try:
            staff_id = request.form.get('staff_id')
            month = request.form.get('month')
            year = int(request.form.get('year'))
            basic_salary = float(request.form.get('basic_salary', 0))
            allowances = float(request.form.get('allowances', 0))
            deductions = float(request.form.get('deductions', 0))
            advance_deduction = float(request.form.get('advance_deduction', 0))
            
            # Calculate net salary
            net_salary = basic_salary + allowances - deductions - advance_deduction
            
            salary = Salary(
                staff_id=staff_id,
                month=month,
                year=year,
                basic_salary=basic_salary,
                allowances=allowances,
                deductions=deductions,
                advance_deduction=advance_deduction,
                net_salary=net_salary,
                status='pending',
                created_by=current_user.id
            )
            
            db.session.add(salary)
            db.session.commit()
            
            flash('Salary record added successfully!', 'success')
            return redirect(url_for('salaries_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding salary: {str(e)}', 'danger')
    
    staff_list = Staff.query.filter_by(status='active').all()
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%B')
    
    return render_template('salaries/add.html',
                         staff_list=staff_list,
                         months=months,
                         current_year=current_year,
                         current_month=current_month)


@app.route('/salaries/<int:salary_id>/pay', methods=['POST'])
@login_required
@role_required('admin')
def pay_salary(salary_id):
    """Mark salary as paid"""
    salary = Salary.query.get_or_404(salary_id)
    
    try:
        salary.status = 'paid'
        salary.payment_date = date.today()
        salary.payment_method = request.form.get('payment_method', 'Bank Transfer')
        salary.payment_reference = request.form.get('payment_reference', '')
        salary.remarks = request.form.get('remarks', '')
        
        db.session.commit()
        flash('Salary marked as paid successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating salary: {str(e)}', 'danger')
    
    return redirect(url_for('salaries_list'))


@app.route('/salaries/<int:salary_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_salary(salary_id):
    """Delete salary record"""
    salary = Salary.query.get_or_404(salary_id)
    
    try:
        db.session.delete(salary)
        db.session.commit()
        flash('Salary record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting salary: {str(e)}', 'danger')
    
    return redirect(url_for('salaries_list'))


# ==================== SALARY ADVANCE ROUTES ====================

@app.route('/salary-advances')
@login_required
@role_required('admin')
def salary_advances_list():
    """List all salary advance requests"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = SalaryAdvance.query
    
    if status_filter:
        query = query.filter(SalaryAdvance.status == status_filter)
    
    advances = query.order_by(SalaryAdvance.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistics
    pending_count = SalaryAdvance.query.filter_by(status='pending').count()
    approved_count = SalaryAdvance.query.filter_by(status='approved').count()
    total_amount = db.session.query(db.func.sum(SalaryAdvance.amount)).filter(
        SalaryAdvance.status.in_(['pending', 'approved', 'paid'])
    ).scalar() or 0
    
    return render_template('salary_advances/list.html',
                         advances=advances,
                         status_filter=status_filter,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         total_amount=float(total_amount))


@app.route('/salary-advances/request', methods=['GET', 'POST'])
@login_required
def request_salary_advance():
    """Request salary advance (staff can request)"""
    if request.method == 'POST':
        try:
            # Get staff profile
            if current_user.role == 'admin':
                staff_id = request.form.get('staff_id')
            else:
                staff = Staff.query.filter_by(user_id=current_user.id).first()
                if not staff:
                    flash('Staff profile not found.', 'danger')
                    return redirect(url_for('dashboard'))
                staff_id = staff.id
            
            amount = float(request.form.get('amount'))
            reason = request.form.get('reason')
            repayment_plan = request.form.get('repayment_plan', 'One-time')
            
            # Get staff to check salary
            staff = Staff.query.get(staff_id)
            if not staff:
                flash('Staff not found.', 'danger')
                return redirect(url_for('request_salary_advance'))
            
            # Validate amount (should not exceed 50% of monthly salary)
            if staff.salary:
                max_advance = float(staff.salary) * 0.5
                if amount > max_advance:
                    flash(f'Advance amount cannot exceed 50% of monthly salary (₦{max_advance:,.2f})', 'danger')
                    return redirect(url_for('request_salary_advance'))
            
            advance = SalaryAdvance(
                staff_id=staff_id,
                amount=amount,
                reason=reason,
                repayment_plan=repayment_plan,
                remaining_amount=amount,
                status='pending'
            )
            
            db.session.add(advance)
            db.session.commit()
            
            flash('Salary advance request submitted successfully!', 'success')
            if current_user.role == 'admin':
                return redirect(url_for('salary_advances_list'))
            else:
                return redirect(url_for('my_salary_advances'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting request: {str(e)}', 'danger')
    
    if current_user.role == 'admin':
        staff_list = Staff.query.filter_by(status='active').all()
    else:
        staff_list = None
        staff = Staff.query.filter_by(user_id=current_user.id).first()
        if not staff:
            flash('Staff profile not found.', 'danger')
            return redirect(url_for('dashboard'))
    
    return render_template('salary_advances/request.html',
                         staff_list=staff_list,
                         staff=staff if current_user.role != 'admin' else None)


@app.route('/salary-advances/<int:advance_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_salary_advance(advance_id):
    """Approve salary advance request"""
    advance = SalaryAdvance.query.get_or_404(advance_id)
    
    try:
        advance.status = 'approved'
        advance.approved_by = current_user.id
        advance.approved_date = date.today()
        advance.remarks = request.form.get('remarks', '')
        
        db.session.commit()
        flash('Salary advance approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving advance: {str(e)}', 'danger')
    
    return redirect(url_for('salary_advances_list'))


@app.route('/salary-advances/<int:advance_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_salary_advance(advance_id):
    """Reject salary advance request"""
    advance = SalaryAdvance.query.get_or_404(advance_id)
    
    try:
        advance.status = 'rejected'
        advance.rejection_reason = request.form.get('rejection_reason', '')
        
        db.session.commit()
        flash('Salary advance rejected.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting advance: {str(e)}', 'danger')
    
    return redirect(url_for('salary_advances_list'))


@app.route('/salary-advances/<int:advance_id>/pay', methods=['POST'])
@login_required
@role_required('admin')
def pay_salary_advance(advance_id):
    """Mark salary advance as paid"""
    advance = SalaryAdvance.query.get_or_404(advance_id)
    
    try:
        advance.status = 'paid'
        advance.payment_date = date.today()
        advance.payment_reference = request.form.get('payment_reference', '')
        advance.remarks = request.form.get('remarks', '')
        
        db.session.commit()
        flash('Salary advance marked as paid!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating advance: {str(e)}', 'danger')
    
    return redirect(url_for('salary_advances_list'))


@app.route('/my-salary-advances')
@login_required
def my_salary_advances():
    """View own salary advance requests (for staff)"""
    staff = Staff.query.filter_by(user_id=current_user.id).first()
    
    if not staff:
        flash('Staff profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    advances = SalaryAdvance.query.filter_by(staff_id=staff.id).order_by(
        SalaryAdvance.created_at.desc()
    ).all()
    
    return render_template('salary_advances/my_advances.html', advances=advances, staff=staff)


# ==================== PORTAL ROUTES ====================
# Parent, Learner, and Teacher Portals


# ==================== PUBLIC ADMISSION APPLICATION ====================

@app.route('/apply', methods=['GET', 'POST'])
def apply_admission():
    """Public admission application form"""
    if request.method == 'POST':
        try:
            # Generate application number
            app_number = f"APP{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
            
            # Handle file uploads
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(os.path.join(upload_folder, 'admissions'), exist_ok=True)
            
            passport_path = None
            birth_cert_path = None
            previous_result_path = None
            medical_report_path = None
            
            if 'passport_photograph' in request.files:
                file = request.files['passport_photograph']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['png', 'jpg', 'jpeg', 'gif']:
                        filename = f"passport_{app_number}.{ext}"
                        filepath = os.path.join(upload_folder, 'admissions', filename)
                        file.save(filepath)
                        passport_path = f"admissions/{filename}"
            
            if 'birth_certificate' in request.files:
                file = request.files['birth_certificate']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['pdf', 'png', 'jpg', 'jpeg']:
                        filename = f"birth_cert_{app_number}.{ext}"
                        filepath = os.path.join(upload_folder, 'admissions', filename)
                        file.save(filepath)
                        birth_cert_path = f"admissions/{filename}"
            
            if 'previous_result' in request.files:
                file = request.files['previous_result']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['pdf', 'png', 'jpg', 'jpeg']:
                        filename = f"result_{app_number}.{ext}"
                        filepath = os.path.join(upload_folder, 'admissions', filename)
                        file.save(filepath)
                        previous_result_path = f"admissions/{filename}"
            
            if 'medical_report' in request.files:
                file = request.files['medical_report']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['pdf', 'png', 'jpg', 'jpeg']:
                        filename = f"medical_{app_number}.{ext}"
                        filepath = os.path.join(upload_folder, 'admissions', filename)
                        file.save(filepath)
                        medical_report_path = f"admissions/{filename}"
            
            # Create application
            application = AdmissionApplication(
                application_number=app_number,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                middle_name=request.form.get('middle_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                address=request.form.get('address'),
                state_of_origin=request.form.get('state_of_origin'),
                lga=request.form.get('lga'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                previous_school=request.form.get('previous_school'),
                class_applying_for=request.form.get('class_applying_for'),
                session=request.form.get('session', '2024/2025'),
                parent_name=request.form.get('parent_name'),
                parent_phone=request.form.get('parent_phone'),
                parent_email=request.form.get('parent_email'),
                parent_address=request.form.get('parent_address'),
                parent_occupation=request.form.get('parent_occupation'),
                relationship=request.form.get('relationship'),
                passport_photograph=passport_path,
                birth_certificate=birth_cert_path,
                previous_result=previous_result_path,
                medical_report=medical_report_path,
                application_fee_amount=5000.00  # Default application fee
            )
            
            db.session.add(application)
            db.session.commit()
            
            flash(f'Application submitted successfully! Your application number is: {app_number}. Please check your email for further instructions.', 'success')
            return redirect(url_for('check_application_status', app_number=app_number))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting application: {str(e)}', 'danger')
    
    # Get current session
    current_session = app.config.get('CURRENT_SESSION', '2024/2025')
    classes = Class.query.filter_by(status='active').all()
    
    return render_template('public/apply.html', current_session=current_session, classes=classes)


@app.route('/check-application/<app_number>')
def check_application_status(app_number):
    """Check admission application status"""
    application = AdmissionApplication.query.filter_by(application_number=app_number).first_or_404()
    return render_template('public/application_status.html', application=application)


# ==================== PARENT PORTAL ====================

@app.route('/parent')
@login_required
@role_required('parent')
def parent_portal():
    """Parent portal dashboard"""
    # Get parent's children (learners)
    # For now, we'll match by parent email or phone
    learners = Learner.query.filter(
        (Learner.parent_email == current_user.email) |
        (Learner.parent_phone == current_user.phone)
    ).all()
    
    # Get statistics
    total_fees_due = 0
    total_fees_paid = 0
    pending_fees = []
    
    for learner in learners:
        learner_fees = Fee.query.filter_by(learner_id=learner.id).all()
        for fee in learner_fees:
            if fee.status == 'pending':
                total_fees_due += float(fee.amount)
                pending_fees.append(fee)
            elif fee.status == 'paid':
                total_fees_paid += float(fee.amount)
    
    return render_template('portals/parent/dashboard.html', 
                         learners=learners, 
                         total_fees_due=total_fees_due,
                         total_fees_paid=total_fees_paid,
                         pending_fees=pending_fees[:5])


@app.route('/parent/children')
@login_required
@role_required('parent')
def parent_children():
    """View all children"""
    learners = Learner.query.filter(
        (Learner.parent_email == current_user.email) |
        (Learner.parent_phone == current_user.phone)
    ).all()
    return render_template('portals/parent/children.html', learners=learners)


@app.route('/parent/child/<int:learner_id>')
@login_required
@role_required('parent')
def parent_child_details(learner_id):
    """View child details"""
    learner = Learner.query.get_or_404(learner_id)
    
    # Verify parent relationship
    if learner.parent_email != current_user.email and learner.parent_phone != current_user.phone:
        flash('You do not have access to this learner\'s information.', 'danger')
        return redirect(url_for('parent_portal'))
    
    # Get learner's fees
    fees = Fee.query.filter_by(learner_id=learner_id).order_by(Fee.created_at.desc()).all()
    
    # Get attendance summary
    attendances = Attendance.query.filter_by(learner_id=learner_id).all()
    total_days = len(attendances)
    present_days = len([a for a in attendances if a.status == 'present'])
    absent_days = len([a for a in attendances if a.status == 'absent'])
    
    return render_template('portals/parent/child_details.html', 
                         learner=learner,
                         fees=fees,
                         total_days=total_days,
                         present_days=present_days,
                         absent_days=absent_days)


@app.route('/parent/fees')
@login_required
@role_required('parent')
def parent_fees():
    """View and pay fees"""
    learners = Learner.query.filter(
        (Learner.parent_email == current_user.email) |
        (Learner.parent_phone == current_user.phone)
    ).all()
    
    all_fees = []
    for learner in learners:
        fees = Fee.query.filter_by(learner_id=learner.id).all()
        for fee in fees:
            fee.learner_name = f"{learner.user.first_name} {learner.user.last_name}"
            all_fees.append(fee)
    
    ewallet = get_or_create_ewallet(current_user.id)
    return render_template('portals/parent/fees.html', fees=all_fees, ewallet=ewallet)


@app.route('/parent/pay-fee/<int:fee_id>', methods=['GET', 'POST'])
@login_required
@role_required('parent')
def parent_pay_fee(fee_id):
    """Pay fee online"""
    fee = Fee.query.get_or_404(fee_id)
    learner = fee.learner
    
    # Verify parent relationship
    if learner.parent_email != current_user.email and learner.parent_phone != current_user.phone:
        flash('You do not have permission to pay this fee.', 'danger')
        return redirect(url_for('parent_fees'))
    
    if fee.status == 'paid':
        flash('This fee has already been paid.', 'info')
        return redirect(url_for('parent_fees'))
    
    # Get e-wallet balance
    ewallet = get_or_create_ewallet(current_user.id)
    can_pay_with_wallet = float(ewallet.balance) >= float(fee.amount)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', '')
        
        if payment_method == 'ewallet':
            # Pay with e-wallet
            return redirect(url_for('ewallet_pay_fee', fee_id=fee_id))
        else:
            # Pay with Flutterwave (direct payment)
            # Generate transaction reference
            trans_ref = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"
            
            # Create payment transaction
            transaction = PaymentTransaction(
                transaction_reference=trans_ref,
                payment_type='fee',
                learner_id=learner.id,
                fee_id=fee.id,
                amount=fee.amount,
                currency='NGN',
                payment_method='flutterwave',
                status='pending',
                payer_name=f"{current_user.first_name} {current_user.last_name}",
                payer_email=current_user.email,
                payer_phone=current_user.phone or learner.parent_phone
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # TODO: Integrate with Flutterwave for direct fee payment
            # For now, redirect to e-wallet deposit if insufficient balance
            flash('Direct payment via Flutterwave coming soon. Please use e-wallet or deposit funds first.', 'info')
            return redirect(url_for('ewallet_deposit'))
    
    return render_template('portals/parent/pay_fee.html', fee=fee, learner=learner, ewallet=ewallet, can_pay_with_wallet=can_pay_with_wallet)


@app.route('/parent/results/<int:learner_id>')
@login_required
@role_required('parent')
def parent_results(learner_id):
    """View child's results"""
    learner = Learner.query.get_or_404(learner_id)
    
    # Verify parent relationship
    if learner.parent_email != current_user.email and learner.parent_phone != current_user.phone:
        flash('You do not have access to this learner\'s results.', 'danger')
        return redirect(url_for('parent_portal'))
    
    # Get results
    exam_results = ExamResult.query.filter_by(learner_id=learner_id).all()
    assignment_results = AssignmentResult.query.filter_by(learner_id=learner_id).all()
    test_results = TestResult.query.filter_by(learner_id=learner_id).all()
    
    return render_template('portals/parent/results.html',
                         learner=learner,
                         exam_results=exam_results,
                         assignment_results=assignment_results,
                         test_results=test_results)


@app.route('/parent/report-card/<int:learner_id>')
@login_required
@role_required('parent')
def parent_report_card(learner_id):
    """Generate and view report card"""
    learner = Learner.query.get_or_404(learner_id)
    
    # Verify parent relationship
    if learner.parent_email != current_user.email and learner.parent_phone != current_user.phone:
        flash('You do not have access to this learner\'s report card.', 'danger')
        return redirect(url_for('parent_portal'))
    
    # Get filters
    session_filter = request.args.get('session', learner.current_session)
    term_filter = request.args.get('term', 'First Term')
    class_filter = request.args.get('class', learner.current_class)
    
    # Get results similar to report_cards route
    assignment_results = AssignmentResult.query.join(Assignment).filter(
        AssignmentResult.learner_id == learner_id,
        Assignment.session == session_filter,
        Assignment.term == term_filter
    ).all()
    
    test_results = TestResult.query.join(Test).filter(
        TestResult.learner_id == learner_id,
        Test.session == session_filter,
        Test.term == term_filter
    ).all()
    
    exam_results = ExamResult.query.join(Exam).filter(
        ExamResult.learner_id == learner_id,
        Exam.session == session_filter,
        Exam.term == term_filter
    ).all()
    
    # Organize by subject
    subject_scores = {}
    for result in assignment_results + test_results + exam_results:
        subject_name = result.assignment.subject.name if hasattr(result, 'assignment') and result.assignment else \
                      result.test.subject.name if hasattr(result, 'test') and result.test else \
                      result.exam.subject.name if hasattr(result, 'exam') and result.exam else 'Unknown'
        
        if subject_name not in subject_scores:
            subject_scores[subject_name] = {'assignments': [], 'tests': [], 'exams': []}
        
        if isinstance(result, AssignmentResult):
            subject_scores[subject_name]['assignments'].append(result)
        elif isinstance(result, TestResult):
            subject_scores[subject_name]['tests'].append(result)
        elif isinstance(result, ExamResult):
            subject_scores[subject_name]['exams'].append(result)
    
    # Calculate totals and averages
    subject_totals = {}
    subject_averages = {}
    overall_total = 0
    overall_count = 0
    
    for subject, scores in subject_scores.items():
        total = sum([float(r.score) for r in scores['assignments'] + scores['tests'] + scores['exams']])
        count = len(scores['assignments'] + scores['tests'] + scores['exams'])
        avg = total / count if count > 0 else 0
        
        subject_totals[subject] = total
        subject_averages[subject] = avg
        overall_total += total
        overall_count += count
    
    overall_average = overall_total / overall_count if overall_count > 0 else 0
    
    return render_template('portals/parent/report_card.html',
                         learner=learner,
                         subject_scores=subject_scores,
                         subject_totals=subject_totals,
                         subject_averages=subject_averages,
                         overall_total=overall_total,
                         overall_average=overall_average,
                         session_filter=session_filter,
                         term_filter=term_filter,
                         class_filter=class_filter)


@app.route('/parent/download-report-card/<int:learner_id>')
@login_required
@role_required('parent')
def parent_download_report_card(learner_id):
    """Download report card as PDF"""
    learner = Learner.query.get_or_404(learner_id)
    
    # Verify parent relationship
    if learner.parent_email != current_user.email and learner.parent_phone != current_user.phone:
        flash('You do not have access to this learner\'s report card.', 'danger')
        return redirect(url_for('parent_portal'))
    
    # Similar logic to download_report_card_pdf route
    # Get filters
    session_filter = request.args.get('session', learner.current_session)
    term_filter = request.args.get('term', 'First Term')
    
    # Get results and generate PDF (simplified version)
    # In production, use the same logic as download_report_card_pdf
    
    flash('PDF download feature coming soon!', 'info')
    return redirect(url_for('parent_report_card', learner_id=learner_id))


# ==================== LEARNER PORTAL ====================

@app.route('/learner')
@login_required
@role_required('learner')
def learner_portal():
    """Learner portal dashboard"""
    learner = Learner.query.filter_by(user_id=current_user.id).first()
    
    if not learner:
        flash('Learner profile not found. Please contact administrator.', 'danger')
        return redirect(url_for('logout'))
    
    # Get statistics
    fees = Fee.query.filter_by(learner_id=learner.id).all()
    total_fees_due = sum([float(f.amount) for f in fees if f.status == 'pending'])
    total_fees_paid = sum([float(f.amount) for f in fees if f.status == 'paid'])
    
    attendances = Attendance.query.filter_by(learner_id=learner.id).all()
    present_days = len([a for a in attendances if a.status == 'present'])
    total_days = len(attendances)
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    return render_template('portals/learner/dashboard.html',
                         learner=learner,
                         total_fees_due=total_fees_due,
                         total_fees_paid=total_fees_paid,
                         attendance_rate=attendance_rate,
                         present_days=present_days,
                         total_days=total_days)


@app.route('/learner/fees')
@login_required
@role_required('learner')
def learner_fees():
    """View fees"""
    learner = Learner.query.filter_by(user_id=current_user.id).first_or_404()
    fees = Fee.query.filter_by(learner_id=learner.id).order_by(Fee.created_at.desc()).all()
    ewallet = get_or_create_ewallet(current_user.id)
    return render_template('portals/learner/fees.html', learner=learner, fees=fees, ewallet=ewallet)


@app.route('/learner/results')
@login_required
@role_required('learner')
def learner_results():
    """View own results"""
    learner = Learner.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get filters
    session_filter = request.args.get('session', learner.current_session)
    term_filter = request.args.get('term', 'First Term')
    
    # Get results
    exam_results = ExamResult.query.join(Exam).filter(
        ExamResult.learner_id == learner.id,
        Exam.session == session_filter,
        Exam.term == term_filter
    ).all()
    
    assignment_results = AssignmentResult.query.join(Assignment).filter(
        AssignmentResult.learner_id == learner.id,
        Assignment.session == session_filter,
        Assignment.term == term_filter
    ).all()
    
    test_results = TestResult.query.join(Test).filter(
        TestResult.learner_id == learner.id,
        Test.session == session_filter,
        Test.term == term_filter
    ).all()
    
    return render_template('portals/learner/results.html',
                         learner=learner,
                         exam_results=exam_results,
                         assignment_results=assignment_results,
                         test_results=test_results,
                         session_filter=session_filter,
                         term_filter=term_filter)


@app.route('/learner/report-card')
@login_required
@role_required('learner')
def learner_report_card():
    """View own report card"""
    learner = Learner.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Similar logic to parent_report_card
    session_filter = request.args.get('session', learner.current_session)
    term_filter = request.args.get('term', 'First Term')
    
    # Get results
    assignment_results = AssignmentResult.query.join(Assignment).filter(
        AssignmentResult.learner_id == learner.id,
        Assignment.session == session_filter,
        Assignment.term == term_filter
    ).all()
    
    test_results = TestResult.query.join(Test).filter(
        TestResult.learner_id == learner.id,
        Test.session == session_filter,
        Test.term == term_filter
    ).all()
    
    exam_results = ExamResult.query.join(Exam).filter(
        ExamResult.learner_id == learner.id,
        Exam.session == session_filter,
        Exam.term == term_filter
    ).all()
    
    # Organize by subject
    subject_scores = {}
    for result in assignment_results + test_results + exam_results:
        subject_name = result.assignment.subject.name if hasattr(result, 'assignment') and result.assignment else \
                      result.test.subject.name if hasattr(result, 'test') and result.test else \
                      result.exam.subject.name if hasattr(result, 'exam') and result.exam else 'Unknown'
        
        if subject_name not in subject_scores:
            subject_scores[subject_name] = {'assignments': [], 'tests': [], 'exams': []}
        
        if isinstance(result, AssignmentResult):
            subject_scores[subject_name]['assignments'].append(result)
        elif isinstance(result, TestResult):
            subject_scores[subject_name]['tests'].append(result)
        elif isinstance(result, ExamResult):
            subject_scores[subject_name]['exams'].append(result)
    
    # Calculate totals
    subject_totals = {}
    subject_averages = {}
    overall_total = 0
    overall_count = 0
    
    for subject, scores in subject_scores.items():
        total = sum([float(r.score) for r in scores['assignments'] + scores['tests'] + scores['exams']])
        count = len(scores['assignments'] + scores['tests'] + scores['exams'])
        avg = total / count if count > 0 else 0
        
        subject_totals[subject] = total
        subject_averages[subject] = avg
        overall_total += total
        overall_count += count
    
    overall_average = overall_total / overall_count if overall_count > 0 else 0
    
    return render_template('portals/learner/report_card.html',
                         learner=learner,
                         subject_scores=subject_scores,
                         subject_totals=subject_totals,
                         subject_averages=subject_averages,
                         overall_total=overall_total,
                         overall_average=overall_average,
                         session_filter=session_filter,
                         term_filter=term_filter)


@app.route('/learner/attendance')
@login_required
@role_required('learner')
def learner_attendance():
    """View own attendance"""
    learner = Learner.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Attendance.query.filter_by(learner_id=learner.id)
    
    if start_date:
        query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    attendances = query.order_by(Attendance.date.desc()).limit(50).all()
    
    # Calculate summary
    total_days = len(attendances)
    present_days = len([a for a in attendances if a.status == 'present'])
    absent_days = len([a for a in attendances if a.status == 'absent'])
    late_days = len([a for a in attendances if a.status == 'late'])
    
    return render_template('portals/learner/attendance.html',
                         learner=learner,
                         attendances=attendances,
                         total_days=total_days,
                         present_days=present_days,
                         absent_days=absent_days,
                         late_days=late_days)


# ==================== TEACHER PORTAL ====================

@app.route('/teacher')
@login_required
@role_required('teacher')
def teacher_portal():
    """Teacher portal dashboard"""
    staff = Staff.query.filter_by(user_id=current_user.id).first()
    
    if not staff:
        flash('Staff profile not found. Please contact administrator.', 'danger')
        return redirect(url_for('logout'))
    
    # Get teacher's classes
    classes = Class.query.filter_by(class_teacher_id=staff.id).all()
    
    # Get statistics
    total_learners = 0
    for cls in classes:
        total_learners += Learner.query.filter_by(current_class=cls.name).count()
    
    # Get recent attendance
    recent_attendances = Attendance.query.join(Learner).filter(
        Learner.current_class.in_([c.name for c in classes])
    ).order_by(Attendance.date.desc()).limit(10).all()
    
    return render_template('portals/teacher/dashboard.html',
                         staff=staff,
                         classes=classes,
                         total_learners=total_learners,
                         recent_attendances=recent_attendances)


@app.route('/teacher/classes')
@login_required
@role_required('teacher')
def teacher_classes():
    """View assigned classes"""
    staff = Staff.query.filter_by(user_id=current_user.id).first_or_404()
    classes = Class.query.filter_by(class_teacher_id=staff.id).all()
    
    # Get learner count for each class
    classes_with_counts = []
    for cls in classes:
        learner_count = Learner.query.filter_by(current_class=cls.name).count()
        classes_with_counts.append({
            'class': cls,
            'learner_count': learner_count
        })
    
    return render_template('portals/teacher/classes.html', 
                         classes_with_counts=classes_with_counts,
                         classes=classes)


@app.route('/teacher/class/<int:class_id>/learners')
@login_required
@role_required('teacher')
def teacher_class_learners(class_id):
    """View learners in a class"""
    cls = Class.query.get_or_404(class_id)
    staff = Staff.query.filter_by(user_id=current_user.id).first()
    
    if cls.class_teacher_id != staff.id:
        flash('You are not assigned to this class.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    learners = Learner.query.filter_by(current_class=cls.name).all()
    return render_template('portals/teacher/class_learners.html', cls=cls, learners=learners)


@app.route('/teacher/results')
@login_required
@role_required('teacher')
def teacher_results():
    """View and manage results"""
    staff = Staff.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get teacher's subjects
    subjects = Subject.query.filter_by(teacher_id=staff.id).all()
    
    # Get results for teacher's subjects
    exam_results = ExamResult.query.join(Exam).filter(
        Exam.subject_id.in_([s.id for s in subjects])
    ).all()
    
    return render_template('portals/teacher/results.html',
                         staff=staff,
                         subjects=subjects,
                         exam_results=exam_results)


# ==================== CASHIER PORTAL ====================

@app.route('/cashier')
@login_required
@role_required('cashier')
def cashier_portal():
    """Cashier portal dashboard"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Today's statistics
    today_fees_paid = Fee.query.filter(
        Fee.paid_date == today,
        Fee.status == 'paid'
    ).all()
    
    today_payments = PaymentTransaction.query.filter(
        PaymentTransaction.payment_date >= start_of_day,
        PaymentTransaction.payment_date <= end_of_day,
        PaymentTransaction.status == 'completed'
    ).all()
    
    today_expenditures = Expenditure.query.filter(
        Expenditure.payment_date == today,
        Expenditure.status == 'paid'
    ).all()
    
    # Calculate totals
    today_fees_total = sum(float(fee.amount) for fee in today_fees_paid)
    today_payments_total = sum(float(payment.amount) for payment in today_payments)
    today_expenditures_total = sum(float(exp.amount) for exp in today_expenditures)
    today_net = today_fees_total + today_payments_total - today_expenditures_total
    
    # Pending fees
    pending_fees = Fee.query.filter_by(status='pending').order_by(Fee.due_date.asc()).limit(10).all()
    pending_fees_count = Fee.query.filter_by(status='pending').count()
    pending_fees_total = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
    
    # Recent transactions
    recent_payments = PaymentTransaction.query.filter(
        PaymentTransaction.status == 'completed'
    ).order_by(PaymentTransaction.payment_date.desc()).limit(10).all()
    
    # Payment methods breakdown for today
    payment_methods = {}
    for fee in today_fees_paid:
        method = fee.payment_method or 'Cash'
        payment_methods[method] = payment_methods.get(method, 0) + float(fee.amount)
    
    for payment in today_payments:
        method = payment.payment_method or 'Online'
        payment_methods[method] = payment_methods.get(method, 0) + float(payment.amount)
    
    stats = {
        'today_fees_total': today_fees_total,
        'today_payments_total': today_payments_total,
        'today_expenditures_total': today_expenditures_total,
        'today_net': today_net,
        'today_fees_count': len(today_fees_paid),
        'today_payments_count': len(today_payments),
        'today_expenditures_count': len(today_expenditures),
        'pending_fees_count': pending_fees_count,
        'pending_fees_total': float(pending_fees_total),
        'payment_methods': payment_methods
    }
    
    return render_template('portals/cashier/dashboard.html',
                         stats=stats,
                         pending_fees=pending_fees,
                         recent_payments=recent_payments,
                         today_fees=today_fees_paid[:5])


@app.route('/cashier/payments')
@login_required
@role_required('cashier')
def cashier_payments():
    """View and process payments"""
    page = request.args.get('page', 1, type=int)
    # Default to pending fees if no status filter is provided
    status_filter = request.args.get('status', '')
    if status_filter == '' and 'status' not in request.args:
        status_filter = 'pending'  # Default to pending on first load
    payment_method = request.args.get('payment_method', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Fee.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if payment_method:
        query = query.filter_by(payment_method=payment_method)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date <= end)
        except:
            pass
    
    fees = query.order_by(Fee.due_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get payment methods for filter
    payment_methods = db.session.query(Fee.payment_method).distinct().all()
    payment_methods = [pm[0] for pm in payment_methods if pm[0]]
    
    return render_template('portals/cashier/payments.html', 
                         fees=fees, 
                         status_filter=status_filter,
                         payment_method=payment_method,
                         start_date=start_date,
                         end_date=end_date,
                         payment_methods=payment_methods)


@app.route('/cashier/payments/<int:fee_id>/process', methods=['GET', 'POST'])
@login_required
@role_required('cashier')
def cashier_process_payment(fee_id):
    """Process fee payment"""
    # Load fee with related learner and user data
    fee = Fee.query.filter_by(id=fee_id).first_or_404()
    # Ensure learner and user are loaded
    if fee.learner:
        _ = fee.learner.user  # Trigger lazy load if needed
    
    if fee.status == 'paid':
        flash('This fee has already been paid.', 'info')
        return redirect(url_for('cashier_payments'))
    
    if request.method == 'POST':
        try:
            payment_method = request.form.get('payment_method', 'Cash')
            receipt_number = request.form.get('receipt_number', '').strip()
            
            # Validate payment method
            if not payment_method:
                flash('Please select a payment method.', 'danger')
                payment_methods_str = app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque')
                payment_methods = [pm.strip() for pm in payment_methods_str.split(',')]
                return render_template('portals/cashier/process_payment.html', 
                                     fee=fee, 
                                     payment_methods=payment_methods)
            
            # Generate receipt number if not provided
            if not receipt_number:
                receipt_number = f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}{fee.id:04d}"
            
            # Check if receipt number already exists
            existing = Fee.query.filter_by(receipt_number=receipt_number).first()
            if existing and existing.id != fee.id:
                flash('Receipt number already exists. Please use a different number.', 'danger')
                payment_methods_str = app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque')
                payment_methods = [pm.strip() for pm in payment_methods_str.split(',')]
                return render_template('portals/cashier/process_payment.html', 
                                     fee=fee, 
                                     payment_methods=payment_methods)
            
            # Update fee
            fee.paid_date = date.today()
            fee.payment_method = payment_method
            fee.receipt_number = receipt_number
            fee.status = 'paid'
            
            # Get learner information safely
            learner_name = f"{fee.learner.user.first_name} {fee.learner.user.last_name}" if fee.learner and fee.learner.user else "Unknown"
            
            # Create payment transaction record
            transaction = PaymentTransaction(
                transaction_reference=receipt_number,
                payment_type='fee',
                learner_id=fee.learner_id,
                fee_id=fee.id,
                amount=fee.amount,
                currency='NGN',
                payment_method=payment_method.lower().replace(' ', '_'),
                status='completed',
                payer_name=learner_name,
                payer_email=fee.learner.parent_email if fee.learner else '',
                payer_phone=fee.learner.parent_phone if fee.learner else '',
                payment_date=datetime.utcnow()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Payment processed successfully! Receipt Number: {receipt_number}', 'success')
            return redirect(url_for('cashier_view_receipt', fee_id=fee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error processing payment: {traceback.format_exc()}')
    
    # Get payment methods from settings
    payment_methods_str = app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque')
    payment_methods = [pm.strip() for pm in payment_methods_str.split(',')]
    
    return render_template('portals/cashier/process_payment.html', 
                         fee=fee, 
                         payment_methods=payment_methods)


@app.route('/cashier/payments/new', methods=['GET', 'POST'])
@login_required
@role_required('cashier')
def cashier_new_payment():
    """Create and process a new payment"""
    if request.method == 'POST':
        try:
            # Get form data
            learner_id = int(request.form.get('learner_id'))
            fee_type = request.form.get('fee_type')
            amount = float(request.form.get('amount', 0))
            due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else date.today()
            session = request.form.get('session', '')
            term = request.form.get('term', '')
            payment_method = request.form.get('payment_method', 'Cash')
            receipt_number = request.form.get('receipt_number', '').strip()
            remarks = request.form.get('remarks', '')
            
            # Validate required fields
            if not learner_id or not fee_type or not amount:
                flash('Please fill in all required fields.', 'danger')
                learners = Learner.query.filter_by(status='active').all()
                payment_methods_str = app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque')
                payment_methods = [pm.strip() for pm in payment_methods_str.split(',')]
                return render_template('portals/cashier/new_payment.html', 
                                     learners=learners, 
                                     payment_methods=payment_methods)
            
            # Create fee
            fee = Fee(
                learner_id=learner_id,
                fee_type=fee_type,
                amount=amount,
                due_date=due_date,
                session=session,
                term=term,
                remarks=remarks,
                status='pending'
            )
            
            db.session.add(fee)
            db.session.flush()  # Get fee.id
            
            # Generate receipt number if not provided
            if not receipt_number:
                receipt_number = f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}{fee.id:04d}"
            
            # Check if receipt number already exists
            existing = Fee.query.filter_by(receipt_number=receipt_number).first()
            if existing:
                receipt_number = f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}{fee.id:04d}"
            
            # Process payment immediately
            fee.paid_date = date.today()
            fee.payment_method = payment_method
            fee.receipt_number = receipt_number
            fee.status = 'paid'
            
            # Get learner information
            learner = Learner.query.get(learner_id)
            learner_name = f"{learner.user.first_name} {learner.user.last_name}" if learner and learner.user else "Unknown"
            
            # Create payment transaction record
            transaction = PaymentTransaction(
                transaction_reference=receipt_number,
                payment_type='fee',
                learner_id=learner_id,
                fee_id=fee.id,
                amount=amount,
                currency='NGN',
                payment_method=payment_method.lower().replace(' ', '_'),
                status='completed',
                payer_name=learner_name,
                payer_email=learner.parent_email if learner else '',
                payer_phone=learner.parent_phone if learner else '',
                payment_date=datetime.utcnow()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Payment processed successfully! Receipt Number: {receipt_number}', 'success')
            return redirect(url_for('cashier_view_receipt', fee_id=fee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}', 'danger')
            import traceback
            app.logger.error(f'Error processing new payment: {traceback.format_exc()}')
    
    # Get active learners
    learners = Learner.query.filter_by(status='active').order_by(Learner.admission_number).all()
    
    # Get payment methods from settings
    payment_methods_str = app.config.get('PAYMENT_METHODS', 'Cash,Bank Transfer,POS,Online Payment,Cheque')
    payment_methods = [pm.strip() for pm in payment_methods_str.split(',')]
    
    # Get current session and term
    current_session = app.config.get('CURRENT_SESSION', datetime.now().strftime('%Y/%Y'))
    current_term = app.config.get('CURRENT_TERM', 'First Term')
    
    return render_template('portals/cashier/new_payment.html',
                         learners=learners,
                         payment_methods=payment_methods,
                         current_session=current_session,
                         current_term=current_term)


@app.route('/cashier/receipt/<int:fee_id>')
@login_required
@role_required('cashier', 'admin', 'accountant')
def cashier_view_receipt(fee_id):
    """View receipt for fee payment"""
    fee = Fee.query.get_or_404(fee_id)
    
    if fee.status != 'paid':
        flash('Receipt can only be generated for paid fees.', 'warning')
        return redirect(url_for('cashier_payments'))
    
    settings = get_school_settings()
    
    return render_template('portals/cashier/receipt.html', fee=fee, settings=settings)


@app.route('/cashier/receipt/<int:fee_id>/print')
@login_required
@role_required('cashier', 'admin', 'accountant')
def cashier_print_receipt(fee_id):
    """Print receipt for fee payment"""
    fee = Fee.query.get_or_404(fee_id)
    
    if fee.status != 'paid':
        flash('Receipt can only be printed for paid fees.', 'warning')
        return redirect(url_for('cashier_payments'))
    
    settings = get_school_settings()
    
    return render_template('portals/cashier/receipt_print.html', fee=fee, settings=settings)


@app.route('/cashier/transactions')
@login_required
@role_required('cashier')
def cashier_transactions():
    """View all payment transactions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    payment_type = request.args.get('payment_type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = PaymentTransaction.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if payment_type:
        query = query.filter_by(payment_type=payment_type)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(PaymentTransaction.payment_date >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(PaymentTransaction.payment_date <= end)
        except:
            pass
    
    transactions = query.order_by(PaymentTransaction.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate totals
    total_amount = db.session.query(db.func.sum(PaymentTransaction.amount)).filter(
        PaymentTransaction.status == 'completed'
    ).scalar() or 0
    
    return render_template('portals/cashier/transactions.html',
                         transactions=transactions,
                         status_filter=status_filter,
                         payment_type=payment_type,
                         start_date=start_date,
                         end_date=end_date,
                         total_amount=float(total_amount))


@app.route('/cashier/daily-summary')
@login_required
@role_required('cashier')
def cashier_daily_summary():
    """Daily cash summary report"""
    selected_date = request.args.get('date', date.today().isoformat())
    
    try:
        summary_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        summary_date = date.today()
    
    # Fees paid on this date
    fees_paid = Fee.query.filter(
        Fee.paid_date == summary_date,
        Fee.status == 'paid'
    ).all()
    
    # Payment transactions on this date
    start_of_day = datetime.combine(summary_date, datetime.min.time())
    end_of_day = datetime.combine(summary_date, datetime.max.time())
    
    transactions = PaymentTransaction.query.filter(
        PaymentTransaction.payment_date >= start_of_day,
        PaymentTransaction.payment_date <= end_of_day,
        PaymentTransaction.status == 'completed'
    ).all()
    
    # Expenditures on this date
    expenditures = Expenditure.query.filter(
        Expenditure.payment_date == summary_date,
        Expenditure.status == 'paid'
    ).all()
    
    # Calculate totals
    fees_total = sum(float(f.amount) for f in fees_paid)
    transactions_total = sum(float(t.amount) for t in transactions)
    expenditures_total = sum(float(e.amount) for e in expenditures)
    total_income = fees_total + transactions_total
    net_cash = total_income - expenditures_total
    
    # Payment method breakdown
    payment_methods = {}
    for fee in fees_paid:
        method = fee.payment_method or 'Cash'
        payment_methods[method] = payment_methods.get(method, 0) + float(fee.amount)
    
    for transaction in transactions:
        method = transaction.payment_method or 'Online'
        payment_methods[method] = payment_methods.get(method, 0) + float(transaction.amount)
    
    stats = {
        'date': summary_date,
        'fees_count': len(fees_paid),
        'fees_total': fees_total,
        'transactions_count': len(transactions),
        'transactions_total': transactions_total,
        'expenditures_count': len(expenditures),
        'expenditures_total': expenditures_total,
        'total_income': total_income,
        'net_cash': net_cash,
        'payment_methods': payment_methods
    }
    
    return render_template('portals/cashier/daily_summary.html',
                         stats=stats,
                         fees=fees_paid,
                         transactions=transactions,
                         expenditures=expenditures)


@app.route('/cashier/reports')
@login_required
@role_required('cashier')
def cashier_reports():
    """Financial reports for cashier"""
    return render_template('portals/cashier/reports.html')


# ID Card Routes
@app.route('/learners/<int:id>/id-card')
@login_required
def learner_id_card(id):
    """Generate and display learner ID card"""
    learner = Learner.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'learner' and learner.user_id != current_user.id:
        flash('You can only view your own ID card.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get school settings
    settings = get_school_settings()
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(learner.admission_number)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    from base64 import b64encode
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = b64encode(qr_buffer.getvalue()).decode()
    
    # Get ID card settings
    id_card_settings = {
        'width': app.config.get('ID_CARD_WIDTH', 500),
        'height': app.config.get('ID_CARD_HEIGHT', 0),
        'border_radius': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'bg_color': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'header_bg_color': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'footer_bg_color': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'border_color': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'border_width': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'logo_position': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'logo_height': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'logo_margin_bottom': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'photo_position': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'photo_width': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'photo_height': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'photo_border_color': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'photo_border_width': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'text_position': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'name_font_size': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'label_font_size': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'value_font_size': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'text_color': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'label_color': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'qr_position': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'qr_size': app.config.get('ID_CARD_QR_SIZE', 120),
        'show_qr': app.config.get('ID_CARD_SHOW_QR', True),
        'header_title_size': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'header_subtitle_size': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'header_text_color': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'footer_text_color': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'footer_font_size': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    return render_template('id_cards/learner.html', 
                         learner=learner, 
                         settings=settings,
                         id_card=id_card_settings,
                         qr_code=qr_base64)


@app.route('/staff/<int:id>/id-card')
@login_required
def staff_id_card(id):
    """Generate and display staff ID card"""
    staff = Staff.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'teacher' and staff.user_id != current_user.id:
        flash('You can only view your own ID card.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get school settings
    settings = get_school_settings()
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(staff.staff_id)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    from base64 import b64encode
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = b64encode(qr_buffer.getvalue()).decode()
    
    # Get ID card settings
    id_card_settings = {
        'width': app.config.get('ID_CARD_WIDTH', 500),
        'height': app.config.get('ID_CARD_HEIGHT', 0),
        'border_radius': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'bg_color': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'header_bg_color': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'footer_bg_color': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'border_color': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'border_width': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'logo_position': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'logo_height': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'logo_margin_bottom': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'photo_position': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'photo_width': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'photo_height': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'photo_border_color': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'photo_border_width': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'text_position': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'name_font_size': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'label_font_size': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'value_font_size': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'text_color': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'label_color': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'qr_position': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'qr_size': app.config.get('ID_CARD_QR_SIZE', 120),
        'show_qr': app.config.get('ID_CARD_SHOW_QR', True),
        'header_title_size': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'header_subtitle_size': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'header_text_color': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'footer_text_color': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'footer_font_size': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    return render_template('id_cards/staff.html', 
                         staff=staff, 
                         settings=settings,
                         id_card=id_card_settings,
                         qr_code=qr_base64)


@app.route('/learners/<int:id>/id-card/print')
@login_required
def print_learner_id_card(id):
    """Print learner ID card"""
    learner = Learner.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'learner' and learner.user_id != current_user.id:
        flash('You can only print your own ID card.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get school settings
    settings = get_school_settings()
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(learner.admission_number)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    from base64 import b64encode
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = b64encode(qr_buffer.getvalue()).decode()
    
    # Get ID card settings
    id_card_settings = {
        'width': app.config.get('ID_CARD_WIDTH', 500),
        'height': app.config.get('ID_CARD_HEIGHT', 0),
        'border_radius': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'bg_color': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'header_bg_color': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'footer_bg_color': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'border_color': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'border_width': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'logo_position': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'logo_height': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'logo_margin_bottom': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'photo_position': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'photo_width': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'photo_height': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'photo_border_color': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'photo_border_width': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'text_position': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'name_font_size': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'label_font_size': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'value_font_size': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'text_color': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'label_color': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'qr_position': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'qr_size': app.config.get('ID_CARD_QR_SIZE', 120),
        'show_qr': app.config.get('ID_CARD_SHOW_QR', True),
        'header_title_size': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'header_subtitle_size': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'header_text_color': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'footer_text_color': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'footer_font_size': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    return render_template('id_cards/learner_print.html', 
                         learner=learner, 
                         settings=settings,
                         id_card=id_card_settings,
                         qr_code=qr_base64)


@app.route('/staff/<int:id>/id-card/print')
@login_required
def print_staff_id_card(id):
    """Print staff ID card"""
    staff = Staff.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'teacher' and staff.user_id != current_user.id:
        flash('You can only print your own ID card.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get school settings
    settings = get_school_settings()
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(staff.staff_id)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    from base64 import b64encode
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_base64 = b64encode(qr_buffer.getvalue()).decode()
    
    # Get ID card settings
    id_card_settings = {
        'width': app.config.get('ID_CARD_WIDTH', 500),
        'height': app.config.get('ID_CARD_HEIGHT', 0),
        'border_radius': app.config.get('ID_CARD_BORDER_RADIUS', 15),
        'bg_color': app.config.get('ID_CARD_BG_COLOR', '#ffffff'),
        'header_bg_color': app.config.get('ID_CARD_HEADER_BG_COLOR', '#32CD32'),
        'footer_bg_color': app.config.get('ID_CARD_FOOTER_BG_COLOR', '#f8f9fa'),
        'border_color': app.config.get('ID_CARD_BORDER_COLOR', '#32CD32'),
        'border_width': app.config.get('ID_CARD_BORDER_WIDTH', 3),
        'logo_position': app.config.get('ID_CARD_LOGO_POSITION', 'top-center'),
        'logo_height': app.config.get('ID_CARD_LOGO_HEIGHT', 60),
        'logo_margin_bottom': app.config.get('ID_CARD_LOGO_MARGIN_BOTTOM', 10),
        'photo_position': app.config.get('ID_CARD_PHOTO_POSITION', 'left'),
        'photo_width': app.config.get('ID_CARD_PHOTO_WIDTH', 150),
        'photo_height': app.config.get('ID_CARD_PHOTO_HEIGHT', 180),
        'photo_border_color': app.config.get('ID_CARD_PHOTO_BORDER_COLOR', '#32CD32'),
        'photo_border_width': app.config.get('ID_CARD_PHOTO_BORDER_WIDTH', 3),
        'text_position': app.config.get('ID_CARD_TEXT_POSITION', 'right'),
        'name_font_size': app.config.get('ID_CARD_NAME_FONT_SIZE', 18),
        'label_font_size': app.config.get('ID_CARD_LABEL_FONT_SIZE', 14),
        'value_font_size': app.config.get('ID_CARD_VALUE_FONT_SIZE', 16),
        'text_color': app.config.get('ID_CARD_TEXT_COLOR', '#000000'),
        'label_color': app.config.get('ID_CARD_LABEL_COLOR', '#666666'),
        'qr_position': app.config.get('ID_CARD_QR_POSITION', 'bottom-center'),
        'qr_size': app.config.get('ID_CARD_QR_SIZE', 120),
        'show_qr': app.config.get('ID_CARD_SHOW_QR', True),
        'header_title_size': app.config.get('ID_CARD_HEADER_TITLE_SIZE', 21),
        'header_subtitle_size': app.config.get('ID_CARD_HEADER_SUBTITLE_SIZE', 14),
        'header_text_color': app.config.get('ID_CARD_HEADER_TEXT_COLOR', '#ffffff'),
        'footer_text_color': app.config.get('ID_CARD_FOOTER_TEXT_COLOR', '#666666'),
        'footer_font_size': app.config.get('ID_CARD_FOOTER_FONT_SIZE', 12),
    }
    
    return render_template('id_cards/staff_print.html', 
                         staff=staff, 
                         settings=settings,
                         id_card=id_card_settings,
                         qr_code=qr_base64)

