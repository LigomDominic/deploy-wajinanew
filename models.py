"""
Database Models for Wajina Suite
"""

from database import db
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, learner, parent, store_keeper, accountant, cashier
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    learner_profile = db.relationship('Learner', backref='user', uselist=False, cascade='all, delete-orphan')
    staff_profile = db.relationship('Staff', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Learner(db.Model):
    """Learner model"""
    __tablename__ = 'learners'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    admission_number = db.Column(db.String(50), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)
    state_of_origin = db.Column(db.String(50))
    lga = db.Column(db.String(100))  # Local Government Area
    blood_group = db.Column(db.String(10))
    parent_name = db.Column(db.String(200))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(120))
    parent_address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))
    admission_date = db.Column(db.Date, default=date.today)
    current_class = db.Column(db.String(50))
    current_session = db.Column(db.String(20))  # e.g., 2024/2025
    passport_photograph = db.Column(db.String(255))  # Path to passport photograph
    status = db.Column(db.String(20), default='active')  # active, graduated, transferred, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='learner', lazy=True, cascade='all, delete-orphan')
    fees = db.relationship('Fee', backref='learner', lazy=True, cascade='all, delete-orphan')
    exam_results = db.relationship('ExamResult', backref='learner', lazy=True, cascade='all, delete-orphan')
    academic_records = db.relationship('AcademicRecord', backref='learner', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Learner {self.admission_number}>'


class Staff(db.Model):
    """Staff/Teacher model"""
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)
    state_of_origin = db.Column(db.String(50))
    lga = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(200))
    specialization = db.Column(db.String(200))
    employment_date = db.Column(db.Date, default=date.today)
    employment_type = db.Column(db.String(20))  # full-time, part-time, contract
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))  # Head Teacher, Deputy Head Teacher, Teacher, etc.
    salary = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='active')  # active, retired, terminated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = db.relationship('Subject', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f'<Staff {self.staff_id}>'


class Class(db.Model):
    """Class model"""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., JSS 1A, SS 2B
    level = db.Column(db.String(20), nullable=False)  # JSS 1, JSS 2, SS 1, SS 2, etc.
    capacity = db.Column(db.Integer, default=40)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    session = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = db.relationship('Subject', backref='class_ref', lazy=True)
    
    def __repr__(self):
        return f'<Class {self.name}>'


class Subject(db.Model):
    """Subject model"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    category = db.Column(db.String(50))  # Core, Elective, etc.
    credit_hours = db.Column(db.Integer, default=1)
    session = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subject {self.name}>'


class Attendance(db.Model):
    """Attendance model"""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    remarks = db.Column(db.Text)
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('learner_id', 'date', name='unique_learner_date'),)
    
    def __repr__(self):
        return f'<Attendance {self.learner_id} - {self.date}>'


class Fee(db.Model):
    """Fee model"""
    __tablename__ = 'fees'
    
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)  # Tuition, PTA, Library, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))  # Cash, Bank Transfer, POS, etc.
    receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    session = db.Column(db.String(20))
    term = db.Column(db.String(20))  # First Term, Second Term, Third Term
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Fee {self.fee_type} - {self.amount}>'


class Exam(db.Model):
    """Exam model"""
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # First Term Exam, WAEC, NECO, etc.
    exam_type = db.Column(db.String(50), nullable=False)  # Internal, WAEC, NECO, JAMB, etc.
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    exam_date = db.Column(db.Date)
    max_score = db.Column(db.Integer, default=100)
    session = db.Column(db.String(20))
    term = db.Column(db.String(20))
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_ref = db.relationship('Class', backref='exams', lazy=True)
    subject = db.relationship('Subject', backref='exams', lazy=True)
    results = db.relationship('ExamResult', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exam {self.name}>'


class ExamResult(db.Model):
    """Exam Result model"""
    __tablename__ = 'exam_results'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    grade = db.Column(db.String(5))  # A, B, C, D, F
    remark = db.Column(db.String(50))  # Excellent, Very Good, Good, Pass, Fail
    position = db.Column(db.Integer)  # Class position
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('exam_id', 'learner_id', name='unique_exam_learner'),)
    
    def __repr__(self):
        return f'<ExamResult {self.learner_id} - {self.score}>'


class Assignment(db.Model):
    """Assignment model"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    assignment_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    max_score = db.Column(db.Integer, default=100)
    session = db.Column(db.String(20))
    term = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='assignments')
    class_obj = db.relationship('Class', backref='assignments')
    creator = db.relationship('User', foreign_keys=[created_by])
    results = db.relationship('AssignmentResult', backref='assignment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.name}>'


class AssignmentResult(db.Model):
    """Assignment Result model"""
    __tablename__ = 'assignment_results'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    grade = db.Column(db.String(5))  # A, B, C, D, F
    remark = db.Column(db.String(50))
    submitted_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('assignment_id', 'learner_id', name='unique_assignment_learner'),)
    
    def __repr__(self):
        return f'<AssignmentResult {self.learner_id} - {self.score}>'


class Test(db.Model):
    """Test model"""
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    test_date = db.Column(db.Date, nullable=False, default=date.today)
    max_score = db.Column(db.Integer, default=100)
    session = db.Column(db.String(20))
    term = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='tests')
    class_obj = db.relationship('Class', backref='tests')
    creator = db.relationship('User', foreign_keys=[created_by])
    results = db.relationship('TestResult', backref='test', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Test {self.name}>'


class TestResult(db.Model):
    """Test Result model"""
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    grade = db.Column(db.String(5))  # A, B, C, D, F
    remark = db.Column(db.String(50))
    position = db.Column(db.Integer)  # Class position
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('test_id', 'learner_id', name='unique_test_learner'),)
    
    def __repr__(self):
        return f'<TestResult {self.learner_id} - {self.score}>'


class AcademicRecord(db.Model):
    """Academic Record model"""
    __tablename__ = 'academic_records'
    
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    session = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    total_score = db.Column(db.Numeric(6, 2))
    average_score = db.Column(db.Numeric(5, 2))
    position = db.Column(db.Integer)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.Text)
    promoted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AcademicRecord {self.learner_id} - {self.session}>'


class StoreItem(db.Model):
    """Store Item model for inventory management"""
    __tablename__ = 'store_items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Equipment, Supplies, Furniture, etc.
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), nullable=False)  # pieces, boxes, kg, liters, etc.
    quantity = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    min_quantity = db.Column(db.Numeric(10, 2), default=0)  # Minimum stock level
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    supplier = db.Column(db.String(200))
    supplier_contact = db.Column(db.String(100))
    location = db.Column(db.String(200))  # Storage location/room
    purchase_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)  # For items with expiry dates
    status = db.Column(db.String(20), default='active')  # active, low_stock, out_of_stock, discontinued
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('StoreTransaction', backref='item', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    @property
    def total_value(self):
        """Calculate total value of stock"""
        return float(self.quantity) * float(self.unit_price)
    
    @property
    def is_low_stock(self):
        """Check if item is low in stock"""
        return float(self.quantity) <= float(self.min_quantity or 0)
    
    def __repr__(self):
        return f'<StoreItem {self.item_name}>'


class StoreTransaction(db.Model):
    """Store Transaction model for tracking stock movements"""
    __tablename__ = 'store_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('store_items.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # in, out, adjustment, return
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2))  # Price at time of transaction
    total_amount = db.Column(db.Numeric(10, 2))
    reference_number = db.Column(db.String(100))  # Invoice, receipt, or reference number
    supplier = db.Column(db.String(200))  # For incoming items
    recipient = db.Column(db.String(200))  # For outgoing items (department, person, etc.)
    purpose = db.Column(db.String(200))  # Purpose of transaction
    notes = db.Column(db.Text)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<StoreTransaction {self.transaction_type} - {self.quantity}>'


class Expenditure(db.Model):
    """Expenditure model for tracking school expenses"""
    __tablename__ = 'expenditures'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)  # Utilities, Salaries, Supplies, Maintenance, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # Cash, Bank Transfer, Cheque, etc.
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    receipt_number = db.Column(db.String(100))
    receipt_file = db.Column(db.String(255))  # Path to uploaded receipt file
    vendor = db.Column(db.String(200))  # Vendor/Supplier name
    vendor_contact = db.Column(db.String(100))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Staff who approved/initiated
    session = db.Column(db.String(20))  # Academic session
    term = db.Column(db.String(20))  # Academic term
    status = db.Column(db.String(20), default='pending')  # pending, approved, paid, rejected
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Expenditure {self.title} - ₦{self.amount}>'


class AdmissionApplication(db.Model):
    """Online admission application model"""
    __tablename__ = 'admission_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text, nullable=False)
    state_of_origin = db.Column(db.String(50))
    lga = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    previous_school = db.Column(db.String(200))
    class_applying_for = db.Column(db.String(50), nullable=False)
    session = db.Column(db.String(20), nullable=False)  # e.g., 2024/2025
    
    # Parent/Guardian Information
    parent_name = db.Column(db.String(200), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    parent_email = db.Column(db.String(120))
    parent_address = db.Column(db.Text)
    parent_occupation = db.Column(db.String(100))
    relationship = db.Column(db.String(50))  # Father, Mother, Guardian
    
    # Documents
    passport_photograph = db.Column(db.String(255))
    birth_certificate = db.Column(db.String(255))
    previous_result = db.Column(db.String(255))
    medical_report = db.Column(db.String(255))
    
    # Application Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, admitted
    remarks = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    
    # Payment
    application_fee_paid = db.Column(db.Boolean, default=False)
    application_fee_amount = db.Column(db.Numeric(10, 2))
    payment_reference = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdmissionApplication {self.application_number}>'


class PaymentTransaction(db.Model):
    """Payment transaction model for online payments"""
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_reference = db.Column(db.String(100), unique=True, nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)  # fee, admission, other
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'))
    fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'))
    admission_application_id = db.Column(db.Integer, db.ForeignKey('admission_applications.id'))
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='NGN')
    payment_method = db.Column(db.String(50))  # card, bank_transfer, online
    payment_gateway = db.Column(db.String(50))  # paystack, flutterwave, etc.
    gateway_reference = db.Column(db.String(100))
    
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    payer_name = db.Column(db.String(200))
    payer_email = db.Column(db.String(120))
    payer_phone = db.Column(db.String(20))
    
    payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    learner = db.relationship('Learner', backref='payment_transactions')
    fee = db.relationship('Fee', backref='payment_transactions')
    admission_application = db.relationship('AdmissionApplication', backref='payment_transactions')
    
    def __repr__(self):
        return f'<PaymentTransaction {self.transaction_reference}>'


class Salary(db.Model):
    """Staff salary model"""
    __tablename__ = 'salaries'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)  # e.g., "January 2024"
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False)
    allowances = db.Column(db.Numeric(10, 2), default=0)  # Housing, transport, etc.
    deductions = db.Column(db.Numeric(10, 2), default=0)  # Tax, pension, etc.
    advance_deduction = db.Column(db.Numeric(10, 2), default=0)  # Salary advance deductions
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))  # Bank Transfer, Cash, Cheque
    payment_reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, paid, cancelled
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = db.relationship('Staff', backref='salaries')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Salary {self.staff.staff_id} - {self.month} {self.year}>'


class SalaryAdvance(db.Model):
    """Salary advance request model"""
    __tablename__ = 'salary_advances'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    request_date = db.Column(db.Date, default=date.today, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    repayment_plan = db.Column(db.String(50))  # One-time, 2 months, 3 months, etc.
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid, completed
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.Date)
    rejection_reason = db.Column(db.Text)
    payment_date = db.Column(db.Date)
    payment_reference = db.Column(db.String(100))
    amount_paid = db.Column(db.Numeric(10, 2), default=0)  # Amount already repaid
    remaining_amount = db.Column(db.Numeric(10, 2))  # Remaining to be repaid
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = db.relationship('Staff', backref='salary_advances')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<SalaryAdvance {self.staff.staff_id} - ₦{self.amount}>'


class SchoolTimetable(db.Model):
    """School Timetable model for regular class schedules"""
    __tablename__ = 'school_timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, Wednesday, etc.
    period = db.Column(db.Integer, nullable=False)  # Period number (1, 2, 3, etc.)
    start_time = db.Column(db.Time, nullable=False)  # e.g., 08:00:00
    end_time = db.Column(db.Time, nullable=False)  # e.g., 08:40:00
    room = db.Column(db.String(50))  # Classroom/Lab name
    session = db.Column(db.String(20))  # Academic session
    term = db.Column(db.String(20))  # Term (First Term, Second Term, Third Term)
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_ref = db.relationship('Class', backref='timetables', lazy=True)
    subject = db.relationship('Subject', backref='timetables', lazy=True)
    teacher = db.relationship('Staff', backref='timetables', lazy=True)
    
    def __repr__(self):
        return f'<SchoolTimetable {self.class_ref.name if self.class_ref else "N/A"} - {self.day_of_week} Period {self.period}>'


class ExamTimetable(db.Model):
    """Exam Timetable model for examination schedules"""
    __tablename__ = 'exam_timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(200), nullable=False)  # e.g., First Term Examination 2024
    exam_type = db.Column(db.String(50), nullable=False)  # Internal, WAEC, NECO, JAMB, etc.
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer)  # Duration in minutes
    room = db.Column(db.String(50))  # Examination hall/room
    invigilator_id = db.Column(db.Integer, db.ForeignKey('staff.id'))  # Invigilator
    session = db.Column(db.String(20))  # Academic session
    term = db.Column(db.String(20))  # Term
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled
    instructions = db.Column(db.Text)  # Special instructions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_ref = db.relationship('Class', backref='exam_timetables', lazy=True)
    subject = db.relationship('Subject', backref='exam_timetables', lazy=True)
    invigilator = db.relationship('Staff', backref='exam_timetables', lazy=True)
    
    def __repr__(self):
        return f'<ExamTimetable {self.exam_name} - {self.subject.name if self.subject else "N/A"}>'


class EWallet(db.Model):
    """E-Wallet model for storing user wallet balances"""
    __tablename__ = 'ewallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    currency = db.Column(db.String(10), default='NGN', nullable=False)
    status = db.Column(db.String(20), default='active')  # active, frozen, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ewallet', uselist=False, lazy=True)
    transactions = db.relationship('EWalletTransaction', backref='ewallet', lazy=True, cascade='all, delete-orphan', order_by='desc(EWalletTransaction.created_at)')
    
    def __repr__(self):
        return f'<EWallet {self.user.username if self.user else "N/A"} - {self.balance}>'


class EWalletTransaction(db.Model):
    """E-Wallet Transaction model for tracking all wallet transactions"""
    __tablename__ = 'ewallet_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    ewallet_id = db.Column(db.Integer, db.ForeignKey('ewallets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, payment, refund, transfer
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    balance_before = db.Column(db.Numeric(10, 2), nullable=False)
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='NGN', nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    payment_method = db.Column(db.String(50))  # flutterwave, bank_transfer, cash, etc.
    payment_gateway = db.Column(db.String(50))  # flutterwave
    transaction_reference = db.Column(db.String(100), unique=True)  # Flutterwave tx_ref or internal ref
    flutterwave_tx_id = db.Column(db.String(100))  # Flutterwave transaction ID
    flutterwave_tx_ref = db.Column(db.String(100))  # Flutterwave transaction reference
    description = db.Column(db.Text)
    related_fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'))  # If used for fee payment
    related_payment_transaction_id = db.Column(db.Integer, db.ForeignKey('payment_transactions.id'))
    transaction_metadata = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ewallet_transactions', lazy=True)
    related_fee = db.relationship('Fee', backref='ewallet_transactions', lazy=True)
    related_payment = db.relationship('PaymentTransaction', backref='ewallet_transactions', lazy=True)
    
    def __repr__(self):
        return f'<EWalletTransaction {self.transaction_type} - {self.amount}>'

