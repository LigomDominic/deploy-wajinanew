"""
Report Generation Utilities for Wajina Suite
Generates PDF and CSV reports
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import csv
from datetime import datetime
import os


def get_school_info():
    """Get school information from Flask app config"""
    try:
        from flask import current_app
        logo_path = ''
        if current_app.config.get('SCHOOL_LOGO'):
            logo_full_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), current_app.config['SCHOOL_LOGO'])
            if os.path.exists(logo_full_path):
                logo_path = logo_full_path
        
        return {
            'school_name': current_app.config.get('SCHOOL_NAME', 'Wajina International School'),
            'school_address': current_app.config.get('SCHOOL_ADDRESS', 'Makurdi, Benue State, Nigeria'),
            'school_phone': current_app.config.get('SCHOOL_PHONE', ''),
            'school_email': current_app.config.get('SCHOOL_EMAIL', ''),
            'school_website': current_app.config.get('SCHOOL_WEBSITE', ''),
            'logo_path': logo_path
        }
    except:
        return {
            'school_name': 'Wajina International School',
            'school_address': 'Makurdi, Benue State, Nigeria',
            'school_phone': '',
            'school_email': '',
            'school_website': '',
            'logo_path': ''
        }


def create_report_header(styles, school_info=None):
    """Create a header with school logo, name, address, and contact"""
    elements = []
    
    if school_info is None:
        school_info = get_school_info()
    
    # Logo
    if school_info.get('logo_path') and os.path.exists(school_info['logo_path']):
        try:
            logo = Image(school_info['logo_path'], width=1.5*inch, height=1.5*inch)
            # Center the logo by wrapping in a table
            logo_table = Table([[logo]], colWidths=[7.5*inch])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.1*inch))
        except Exception as e:
            # If logo fails to load, continue without it
            import traceback
            print(f"Error loading logo: {e}")
            traceback.print_exc()
            pass
    
    # School name
    title_style = ParagraphStyle(
        'SchoolTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#9ACD32'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(school_info.get('school_name', 'Wajina International School'), title_style))
    
    # Address and contact
    contact_info = school_info.get('school_address', 'Makurdi, Benue State, Nigeria')
    if school_info.get('school_phone'):
        contact_info += f" | Phone: {school_info['school_phone']}"
    if school_info.get('school_email'):
        contact_info += f" | Email: {school_info['school_email']}"
    if school_info.get('school_website'):
        contact_info += f" | Website: {school_info['school_website']}"
    
    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    elements.append(Paragraph(contact_info, contact_style))
    
    # Horizontal line
    elements.append(Spacer(1, 0.1*inch))
    
    return elements


def generate_learner_pdf(learners, filters=None, school_info=None):
    """Generate PDF report for learners"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Create header
    header_elements = create_report_header(styles, school_info)
    elements.extend(header_elements)
    
    # Title
    title = Paragraph("LEARNER REPORT", styles['Heading1'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Filters info
    if filters:
        filter_text = "Filters: "
        if filters.get('class'):
            filter_text += f"Class: {filters['class']} | "
        if filters.get('status'):
            filter_text += f"Status: {filters['status']} | "
        if filters.get('search'):
            filter_text += f"Search: {filters['search']}"
        elements.append(Paragraph(filter_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [['Admission No.', 'Name', 'Class', 'Gender', 'Status']]
    
    for learner in learners:
        table_data.append([
            learner.admission_number,
            f"{learner.user.first_name} {learner.user.last_name}",
            learner.current_class or 'N/A',
            learner.gender,
            learner.status
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_attendance_pdf(attendance_data, filters=None, school_info=None):
    """Generate PDF report for attendance"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Create header
    header_elements = create_report_header(styles, school_info)
    elements.extend(header_elements)
    
    # Title
    title = Paragraph("ATTENDANCE REPORT", styles['Heading1'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Statistics
    if filters:
        stats_text = f"Total Days: {filters.get('total_days', 0)} | "
        stats_text += f"Present: {filters.get('present_count', 0)} | "
        stats_text += f"Absent: {filters.get('absent_count', 0)} | "
        stats_text += f"Late: {filters.get('late_count', 0)}"
        elements.append(Paragraph(stats_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [['Learner', 'Class', 'Present', 'Absent', 'Late', 'Attendance %']]
    
    for data in attendance_data:
        learner_name = f"{data['learner'].user.first_name} {data['learner'].user.last_name}"
        present = data.get('present', 0)
        absent = data.get('absent', 0)
        late = data.get('late', 0)
        total = present + absent + late
        percentage = (present / total * 100) if total > 0 else 0
        
        table_data.append([
            learner_name,
            data['learner'].current_class or 'N/A',
            str(present),
            str(absent),
            str(late),
            f"{percentage:.1f}%"
        ])
    
    # Create table
    table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_fee_pdf(fees, filters=None, school_info=None):
    """Generate PDF report for fees"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Create header
    header_elements = create_report_header(styles, school_info)
    elements.extend(header_elements)
    
    # Title
    title = Paragraph("FEE REPORT", styles['Heading1'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    table_data = [['Learner', 'Fee Type', 'Amount', 'Due Date', 'Paid Date', 'Status']]
    
    total_amount = 0
    for fee in fees:
        learner_name = f"{fee.learner.user.first_name} {fee.learner.user.last_name}"
        table_data.append([
            learner_name,
            fee.fee_type,
            f"₦{float(fee.amount):,.2f}",
            fee.due_date.strftime('%d/%m/%Y') if fee.due_date else 'N/A',
            fee.paid_date.strftime('%d/%m/%Y') if fee.paid_date else 'N/A',
            fee.status
        ])
        total_amount += float(fee.amount)
    
    # Add total row
    table_data.append(['TOTAL', '', f"₦{total_amount:,.2f}", '', '', ''])
    
    # Create table
    table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_learner_csv(learners, filters=None):
    """Generate CSV report for learners"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Admission Number', 'First Name', 'Last Name', 'Class', 'Gender', 'Status'])
    
    # Data rows
    for learner in learners:
        writer.writerow([
            learner.admission_number,
            learner.user.first_name,
            learner.user.last_name,
            learner.current_class or 'N/A',
            learner.gender,
            learner.status
        ])
    
    buffer.seek(0)
    return buffer


def generate_attendance_csv(attendance_data, filters=None):
    """Generate CSV report for attendance"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Learner Name', 'Admission Number', 'Class', 'Present', 'Absent', 'Late', 'Attendance %'])
    
    # Data rows
    for data in attendance_data:
        learner = data['learner']
        present = data.get('present', 0)
        absent = data.get('absent', 0)
        late = data.get('late', 0)
        total = present + absent + late
        percentage = (present / total * 100) if total > 0 else 0
        
        writer.writerow([
            f"{learner.user.first_name} {learner.user.last_name}",
            learner.admission_number,
            learner.current_class or 'N/A',
            present,
            absent,
            late,
            f"{percentage:.1f}%"
        ])
    
    buffer.seek(0)
    return buffer


def generate_fee_csv(fees, filters=None):
    """Generate CSV report for fees"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Learner Name', 'Admission Number', 'Fee Type', 'Amount', 'Due Date', 'Paid Date', 'Status'])
    
    # Data rows
    for fee in fees:
        writer.writerow([
            f"{fee.learner.user.first_name} {fee.learner.user.last_name}",
            fee.learner.admission_number,
            fee.fee_type,
            float(fee.amount),
            fee.due_date.strftime('%d/%m/%Y') if fee.due_date else 'N/A',
            fee.paid_date.strftime('%d/%m/%Y') if fee.paid_date else 'N/A',
            fee.status
        ])
    
    buffer.seek(0)
    return buffer


def generate_store_pdf(items, filters=None, school_info=None):
    """Generate PDF report for store items"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Create header
    header_elements = create_report_header(styles, school_info)
    elements.extend(header_elements)
    
    # Title
    title = Paragraph("STORE INVENTORY REPORT", styles['Heading1'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Statistics
    if filters:
        stats_text = f"Total Items: {filters.get('total_items', 0)} | "
        stats_text += f"Total Value: ₦{filters.get('total_value', 0):,.2f} | "
        stats_text += f"Low Stock: {filters.get('low_stock', 0)} | "
        stats_text += f"Out of Stock: {filters.get('out_of_stock', 0)}"
        elements.append(Paragraph(stats_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [['Item Code', 'Item Name', 'Category', 'Quantity', 'Unit', 'Unit Price', 'Total Value', 'Status']]
    
    for item in items:
        table_data.append([
            item.item_code,
            item.item_name,
            item.category,
            str(item.quantity),
            item.unit,
            f"₦{float(item.unit_price):,.2f}",
            f"₦{float(item.total_value):,.2f}",
            item.status
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1*inch, 2*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 1.2*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_expenditure_pdf(expenditures, filters=None, school_info=None):
    """Generate PDF report for expenditures"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Create header
    header_elements = create_report_header(styles, school_info)
    elements.extend(header_elements)
    
    # Title
    title = Paragraph("EXPENDITURE REPORT", styles['Heading1'])
    title.hAlign = 'CENTER'
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Statistics
    if filters:
        stats_text = f"Total Amount: ₦{filters.get('total_amount', 0):,.2f} | "
        stats_text += f"Paid: ₦{filters.get('paid_amount', 0):,.2f} | "
        stats_text += f"Pending: ₦{filters.get('pending_amount', 0):,.2f}"
        elements.append(Paragraph(stats_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [['Expense Code', 'Title', 'Category', 'Amount', 'Payment Date', 'Status', 'Approved By']]
    
    for exp in expenditures:
        approver_name = f"{exp.approver.first_name} {exp.approver.last_name}" if exp.approver else 'N/A'
        table_data.append([
            exp.expense_code,
            exp.title,
            exp.category,
            f"₦{float(exp.amount):,.2f}",
            exp.payment_date.strftime('%d/%m/%Y') if exp.payment_date else 'N/A',
            exp.status,
            approver_name
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_store_csv(items, filters=None):
    """Generate CSV report for store items"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Item Code', 'Item Name', 'Category', 'Quantity', 'Unit', 'Unit Price', 'Total Value', 'Status'])
    
    # Data rows
    for item in items:
        writer.writerow([
            item.item_code,
            item.item_name,
            item.category,
            item.quantity,
            item.unit,
            float(item.unit_price),
            float(item.total_value),
            item.status
        ])
    
    buffer.seek(0)
    return buffer


def generate_expenditure_csv(expenditures, filters=None):
    """Generate CSV report for expenditures"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Expense Code', 'Title', 'Category', 'Amount', 'Payment Date', 'Payment Method',
                     'Receipt Number', 'Vendor', 'Status', 'Approved By', 'Session', 'Term'])
    
    # Data rows
    for exp in expenditures:
        approver_name = f"{exp.approver.first_name} {exp.approver.last_name}" if exp.approver else 'N/A'
        writer.writerow([
            exp.expense_code,
            exp.title,
            exp.category,
            float(exp.amount),
            exp.payment_date.strftime('%d/%m/%Y') if exp.payment_date else 'N/A',
            exp.payment_method or 'N/A',
            exp.receipt_number or 'N/A',
            exp.vendor or 'N/A',
            exp.status,
            approver_name,
            exp.session or 'N/A',
            exp.term or 'N/A'
        ])
    
    buffer.seek(0)
    return buffer


def generate_report_card_pdf(learners_data, filters=None, school_info=None):
    """Generate PDF report cards for learners"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get school info if not provided
    if school_info is None:
        school_info = get_school_info()
    
    # Process each learner
    for learner_data in learners_data:
        # Create header for each learner
        header_elements = create_report_header(styles, school_info)
        elements.extend(header_elements)
        
        learner = learner_data['learner']
        assessments = learner_data.get('assessments', {})
        totals = learner_data.get('totals', 0)
        averages = learner_data.get('averages', 0)
        position = learner_data.get('position')
        subjects_dict = learner_data.get('subjects_dict', {})
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#9ACD32'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("TERMLY REPORT CARD", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Learner Information
        info_data = [
            ['Name:', f"{learner.user.first_name} {learner.user.last_name}", 'Admission Number:', learner.admission_number],
            ['Class:', learner.current_class or 'N/A', 'Session:', filters.get('session', 'N/A') if filters else 'N/A'],
            ['Term:', filters.get('term', 'N/A') if filters else 'N/A', 'Date of Birth:', learner.date_of_birth.strftime('%d/%m/%Y') if learner.date_of_birth else 'N/A'],
        ]
        info_table = Table(info_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary Cards
        pos_str = f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}" if position else 'N/A'
        summary_data = [
            ['Total Score', 'Average Score', 'Class Position'],
            [f"{totals:.2f}", f"{averages:.2f}%", pos_str]
        ]
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Subject-wise Performance
        subject_scores = assessments.get('subject_scores', {})
        subject_totals = assessments.get('subject_totals', {})
        subject_averages = assessments.get('subject_averages', {})
        
        if subject_scores:
            # Table header
            table_data = [['Subject', 'Assignments', 'Tests', 'Exams', 'Total', 'Average', 'Grade']]
            
            for subject_id, scores in subject_scores.items():
                subject_name = subjects_dict.get(subject_id, 'N/A')
                
                # Format assignments
                assignments_str = ""
                for a in scores.get('assignments', []):
                    assignments_str += f"{a['name']}: {a['score']:.1f}/{a['max_score']} ({a['grade']})\n"
                if not assignments_str:
                    assignments_str = "No assignments"
                
                # Format tests
                tests_str = ""
                for t in scores.get('tests', []):
                    tests_str += f"{t['name']}: {t['score']:.1f}/{t['max_score']} ({t['grade']})\n"
                if not tests_str:
                    tests_str = "No tests"
                
                # Format exams
                exams_str = ""
                for e in scores.get('exams', []):
                    exams_str += f"{e['name']}: {e['score']:.1f}/{e['max_score']} ({e['grade']})\n"
                if not exams_str:
                    exams_str = "No exams"
                
                total = subject_totals.get(subject_id, 0)
                avg = subject_averages.get(subject_id, 0)
                
                # Determine grade
                if avg >= 75:
                    grade = 'A'
                elif avg >= 65:
                    grade = 'B'
                elif avg >= 55:
                    grade = 'C'
                elif avg >= 45:
                    grade = 'D'
                else:
                    grade = 'F'
                
                table_data.append([
                    subject_name,
                    assignments_str.strip(),
                    tests_str.strip(),
                    exams_str.strip(),
                    f"{total:.2f}",
                    f"{avg:.2f}%",
                    grade
                ])
            
            # Create table
            subject_table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.7*inch])
            subject_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ACD32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(subject_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Overall Grade
        if averages >= 75:
            overall_grade = 'A'
            remark = 'Excellent'
        elif averages >= 65:
            overall_grade = 'B'
            remark = 'Very Good'
        elif averages >= 55:
            overall_grade = 'C'
            remark = 'Good'
        elif averages >= 45:
            overall_grade = 'D'
            remark = 'Fair'
        else:
            overall_grade = 'F'
            remark = 'Needs Improvement'
        
        grade_style = ParagraphStyle(
            'OverallGrade',
            parent=styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#9ACD32'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Overall Grade: {overall_grade} ({remark})", grade_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Signatures
        signature_data = [
            ['Class Teacher\'s Signature:', 'Parent/Guardian\'s Signature:', 'Head Teacher\'s Signature:'],
            ['_________________', '_________________', '_________________']
        ]
        sig_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (1, 0), (-1, 0), 30),
        ]))
        elements.append(sig_table)
        
        # Page break between learners - ensure each report card is on its own page
        # Add extra spacing before page break to ensure clean separation
        elements.append(Spacer(1, 0.5*inch))
        elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_report_card_csv(learners_data, filters=None):
    """Generate CSV report cards for learners"""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow(['Report Card - Termly Assessment Results'])
    writer.writerow([])
    
    # Process each learner
    for learner_data in learners_data:
        learner = learner_data['learner']
        assessments = learner_data.get('assessments', {})
        totals = learner_data.get('totals', 0)
        averages = learner_data.get('averages', 0)
        position = learner_data.get('position')
        subjects_dict = learner_data.get('subjects_dict', {})
        
        writer.writerow(['=' * 80])
        writer.writerow(['LEARNER INFORMATION'])
        writer.writerow(['=' * 80])
        writer.writerow(['Name:', f"{learner.user.first_name} {learner.user.last_name}"])
        writer.writerow(['Admission Number:', learner.admission_number])
        writer.writerow(['Class:', learner.current_class or 'N/A'])
        writer.writerow(['Session:', filters.get('session', 'N/A') if filters else 'N/A'])
        writer.writerow(['Term:', filters.get('term', 'N/A') if filters else 'N/A'])
        writer.writerow(['Total Score:', f"{totals:.2f}"])
        writer.writerow(['Average Score:', f"{averages:.2f}%"])
        pos_str = f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}" if position else 'N/A'
        writer.writerow(['Class Position:', pos_str])
        writer.writerow([])
        
        # Subject-wise breakdown
        subject_scores = assessments.get('subject_scores', {})
        subject_totals = assessments.get('subject_totals', {})
        subject_averages = assessments.get('subject_averages', {})
        
        if subject_scores:
            writer.writerow(['SUBJECT-WISE PERFORMANCE'])
            writer.writerow(['-' * 80])
            writer.writerow(['Subject', 'Assignments', 'Tests', 'Exams', 'Total Score', 'Average', 'Grade'])
            
            for subject_id, scores in subject_scores.items():
                subject_name = subjects_dict.get(subject_id, 'N/A')
                
                # Format assessments
                assignments = ', '.join([f"{a['name']} ({a['score']:.1f}/{a['max_score']})" for a in scores.get('assignments', [])]) or 'None'
                tests = ', '.join([f"{t['name']} ({t['score']:.1f}/{t['max_score']})" for t in scores.get('tests', [])]) or 'None'
                exams = ', '.join([f"{e['name']} ({e['score']:.1f}/{e['max_score']})" for e in scores.get('exams', [])]) or 'None'
                
                total = subject_totals.get(subject_id, 0)
                avg = subject_averages.get(subject_id, 0)
                
                # Determine grade
                if avg >= 75:
                    grade = 'A'
                elif avg >= 65:
                    grade = 'B'
                elif avg >= 55:
                    grade = 'C'
                elif avg >= 45:
                    grade = 'D'
                else:
                    grade = 'F'
                
                writer.writerow([subject_name, assignments, tests, exams, f"{total:.2f}", f"{avg:.2f}%", grade])
            
            writer.writerow([])
        
        writer.writerow([])
    
    buffer.seek(0)
    return buffer
