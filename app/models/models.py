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
    date_of_birth = db.Column('DateOfBirth', db.Date, nullable=False)
    telegram_id = db.Column('TelegramId', db.String, nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    parent_students = relationship('ParentStudentRelation', foreign_keys='[ParentStudentRelation.parent_id]', back_populates='parent', cascade="all, delete-orphan")
    student_parents = relationship('ParentStudentRelation', foreign_keys='[ParentStudentRelation.student_id]', back_populates='student', cascade="all, delete-orphan")
    class_assignments_as_teacher = relationship('ClassAssignment', foreign_keys='ClassAssignment.teacher_id', back_populates='teacher')
    class_assignments_as_student = relationship('ClassAssignment', foreign_keys='ClassAssignment.student_id', back_populates='student')


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
    total_fee = db.Column('TotalFee', db.Numeric(10, 2), nullable=False)

    # Relationships
    discounts = relationship('Discounts', back_populates='fee_structure')
    late_penalties = relationship('LatePenalties', back_populates='fee_structure')
    student_fee_assignments = relationship('StudentFeeAssignment', back_populates='fee_structure')


# LatePenalties model
class LatePenalties(db.Model):
    __tablename__ = 'LatePenalties'
    penalty_id = db.Column('PenaltyId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='CASCADE'))
    penalty_amount = db.Column('PenaltyAmount', db.Numeric(10, 2), nullable=False)

    # Relationship
    fee_structure = relationship('FeeStructure', back_populates='late_penalties')


# Invoice model
class Invoice(db.Model):
    __tablename__ = 'Invoice'
    invoice_id = db.Column('InvoiceId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_date = db.Column('InvoiceDate', db.Date, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    total_amount = db.Column('TotalAmount', db.Numeric(10, 2), nullable=False)
    status_id = db.Column('StatusId', db.String, ForeignKey('PaymentStatus.StatusId', ondelete='SET NULL'))

    # Relationships
    fee_records = relationship('FeeRecord', back_populates='invoice')
    receipts = relationship('Receipt', back_populates='invoice')
    payment_status = relationship('PaymentStatus', back_populates='invoices')


# FeeRecord model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_id = db.Column('FeeId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount_due = db.Column('AmountDue', db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column('AmountPaid', db.Numeric(10, 2), nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    invoice_id = db.Column('InvoiceId', db.String, ForeignKey('Invoice.InvoiceId', ondelete='SET NULL'))
    fee_assignment_id = db.Column('FeeAssignmentId', db.String, ForeignKey('StudentFeeAssignment.FeeAssignmentId', ondelete='SET NULL'))

    # Relationships
    invoice = relationship('Invoice', back_populates='fee_records')
    student_fee_assignments = relationship('StudentFeeAssignment', back_populates='fee_records')


# PaymentStatus model
class PaymentStatus(db.Model):
    __tablename__ = 'PaymentStatus'
    status_id = db.Column('StatusId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status_name = db.Column('StatusName', db.String, nullable=False)

    # Relationships
    invoices = relationship('Invoice', back_populates='payment_status')


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
    amount_paid = db.Column('AmountPaid', db.Numeric(10, 2), nullable=False)
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

    # Relationships
    users = relationship('User')
    fee_structure = relationship('FeeStructure', back_populates='student_fee_assignments')
    fee_records = relationship('FeeRecord', back_populates='student_fee_assignments')
