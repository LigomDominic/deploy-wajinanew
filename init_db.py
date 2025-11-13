"""
Database initialization script for Render deployment
This script initializes the database tables and creates default admin user
"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect, text

def init_database():
    """Initialize database tables and create default admin user"""
    with app.app_context():
        print("Initializing database...")
        
        # Load settings from file if available
        try:
            from routes import load_settings_from_file
            load_settings_from_file()
        except Exception as e:
            print(f"Note: Could not load settings from file: {str(e)}")
        
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Add passport_photograph column if it doesn't exist
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('learners')]
            
            if 'passport_photograph' not in columns:
                print("Adding passport_photograph column to learners table...")
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE learners ADD COLUMN passport_photograph VARCHAR(255)'))
                print("Column added successfully!")
        except Exception as e:
            print(f"Note: Could not add passport_photograph column automatically: {str(e)}")
        
        # Add receipt_file column to expenditures table if it doesn't exist
        try:
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
            print("IMPORTANT: Change this password after first login!")
            print("=" * 50)
        else:
            print("Admin user already exists.")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_database()

