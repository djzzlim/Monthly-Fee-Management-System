from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy import Numeric, Date, String, ForeignKey, Column, Boolean
import uuid


# Role model
class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('Id', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_name = db.Column('RoleName', db.String, nullable=False)
    
    # Relationship
    users = relationship('User', back_populates='role')


# User model
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column('Id', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    password = db.Column('Password', db.String, nullable=True)
    role_id = db.Column('RoleId', db.String, ForeignKey('Role.Id', ondelete='SET NULL'))
    email = db.Column('Email', db.String, nullable=False)
    first_name = db.Column('FirstName', db.String, nullable=False)
    last_name = db.Column('LastName', db.String, nullable=False)
    date_of_birth = db.Column('DateOfBirth', db.Date, nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    created_fee_records = db.relationship('FeeRecord', foreign_keys='FeeRecord.created_by', backref='creator')
    invoices = relationship('Invoice', back_populates='created_by_user')
    parent_students = relationship('ParentStudentRelation', foreign_keys='[ParentStudentRelation.parent_id]', back_populates='parent', cascade="all, delete-orphan")
    student_parents = relationship('ParentStudentRelation', foreign_keys='[ParentStudentRelation.student_id]', back_populates='student', cascade="all, delete-orphan")
    
    # Separate relationships for teachers and students in ClassAssignment
    class_assignments_as_teacher = relationship(
        'ClassAssignment', foreign_keys='ClassAssignment.teacher_id', back_populates='teacher'
    )
    class_assignments_as_student = relationship(
        'ClassAssignment', foreign_keys='ClassAssignment.student_id', back_populates='student'
    )

# ParentStudentRelation association table
class ParentStudentRelation(db.Model):
    __tablename__ = 'ParentStudentRelation'
    parent_id = db.Column('ParentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), primary_key=True)
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), primary_key=True)

    # Relationships
    parent = relationship('User', foreign_keys=[parent_id], back_populates='parent_students')
    student = relationship('User', foreign_keys=[student_id], back_populates='student_parents')


# FeeStructure model
class FeeStructure(db.Model):
    __tablename__ = 'FeeStructure'
    structure_id = db.Column('StructureId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    description = db.Column('Description', db.String, nullable=False)
    total_fee = db.Column('TotalFee', db.Numeric, nullable=False)
    
    # Relationships
    fee_records = relationship('FeeRecord', back_populates='fee_structure')
    discounts = relationship('Discounts', back_populates='fee_structure')
    late_penalties = relationship('LatePenalties', back_populates='fee_structure')


# Discounts model
class Discounts(db.Model):
    __tablename__ = 'Discounts'
    discount_id = db.Column('DiscountId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='CASCADE'))
    discount_amount = db.Column('DiscountAmount', db.Numeric, nullable=False)
    
    # Relationship
    fee_structure = relationship('FeeStructure', back_populates='discounts')


# LatePenalties model
class LatePenalties(db.Model):
    __tablename__ = 'LatePenalties'
    penalty_id = db.Column('PenaltyId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='CASCADE'))
    penalty_amount = db.Column('PenaltyAmount', db.Numeric, nullable=False)
    
    # Relationship
    fee_structure = relationship('FeeStructure', back_populates='late_penalties')


# Invoice model
class Invoice(db.Model):
    __tablename__ = 'Invoice'
    invoice_id = db.Column('InvoiceId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_date = db.Column('InvoiceDate', db.Date, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    total_amount = db.Column('TotalAmount', db.Numeric, nullable=False)
    status_id = db.Column('StatusId', db.String, ForeignKey('PaymentStatus.StatusId', ondelete='SET NULL'))
    created_by = db.Column('CreatedBy', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    
    # Relationships
    fee_records = relationship('FeeRecord', back_populates='invoice')
    created_by_user = relationship('User', back_populates='invoices')
    receipts = relationship('Receipt', back_populates='invoice')


# FeeRecord model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_id = db.Column('FeeId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), nullable=False)
    amount_due = db.Column('AmountDue', db.Numeric, nullable=False)
    amount_paid = db.Column('AmountPaid', db.Numeric, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    invoice_id = db.Column('InvoiceId', db.String, ForeignKey('Invoice.InvoiceId', ondelete='SET NULL'))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId'))
    created_by = db.Column('CreatedBy', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    
    # Relationships
    invoice = relationship('Invoice', back_populates='fee_records')
    fee_structure = relationship('FeeStructure', back_populates='fee_records')
    student = relationship('User', foreign_keys=[student_id])  
    created_by_user = relationship('User', back_populates='created_fee_records', foreign_keys=[created_by])


# PaymentStatus model
class PaymentStatus(db.Model):
    __tablename__ = 'PaymentStatus'
    status_id = db.Column('StatusId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status_name = db.Column('StatusName', db.String, nullable=False)
    
    # Relationships
    invoices = relationship('Invoice', backref='payment_status')


# Class model
class Class(db.Model):
    __tablename__ = 'Class'
    class_id = db.Column('ClassId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_name = db.Column('ClassName', db.String, nullable=False)
    description = db.Column('Description', db.String)

    # Relationships
    assignments = relationship('ClassAssignment', back_populates='class_')


# ClassAssignment model
class ClassAssignment(db.Model):
    __tablename__ = 'ClassAssignment'
    assignment_id = db.Column('AssignmentId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column('ClassId', db.String, ForeignKey('Class.ClassId', ondelete='CASCADE'))
    teacher_id = db.Column('TeacherId', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    assignment_date = db.Column('AssignmentDate', db.Date, default=db.func.current_date())

    # Relationships
    class_ = relationship('Class', back_populates='assignments')
    teacher = relationship('User', foreign_keys=[teacher_id], back_populates='class_assignments_as_teacher')
    student = relationship('User', foreign_keys=[student_id], back_populates='class_assignments_as_student')

# Receipt model
class Receipt(db.Model):
    __tablename__ = 'Receipt'
    receipt_id = db.Column('ReceiptId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column('InvoiceId', db.String, ForeignKey('Invoice.InvoiceId', ondelete='SET NULL'))
    amount_paid = db.Column('AmountPaid', db.Numeric, nullable=False)
    payment_date = db.Column('PaymentDate', db.Date, default=db.func.current_date())
    payment_method = db.Column('PaymentMethod', db.String)

    # Relationships
    invoice = relationship('Invoice', back_populates='receipts')


# Settings model
class Settings(db.Model):
    __tablename__ = 'Settings'
    setting_key = db.Column('SettingKey', db.String, primary_key=True)
    setting_value = db.Column('SettingValue', db.String)
    description = db.Column('Description', db.String, nullable=False)
    value_type = db.Column('ValueType', db.String, nullable=False)
    category = db.Column('Category', db.String, nullable=False)


# StudentFeeAssignment model
class StudentFeeAssignment(db.Model):
    __tablename__ = 'StudentFeeAssignment'
    fee_assignment_id = db.Column('FeeAssignmentId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId'))
    assigned_date = db.Column('AssignedDate', db.Date, nullable=False)
    
    # Relationships
    student = relationship('User', backref='fee_assignments')
    fee_structure = relationship('FeeStructure')
