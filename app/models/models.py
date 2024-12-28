from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid

# Role model
class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('Id', db.String, primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    role_name = db.Column('RoleName', db.String, nullable=False)

    # Relationship
    users = relationship('User', back_populates='role')


# User model
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column('Id', db.String, primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    password = db.Column('Password', db.String, nullable=True)
    role_id = db.Column('RoleId', db.String, ForeignKey(
        'Role.Id', ondelete='SET NULL'))
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
    relation_id = db.Column('RelationId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = db.Column('ParentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))

    # Relationships
    parent = relationship('User', foreign_keys=[parent_id], back_populates='parent_students')
    student = relationship('User', foreign_keys=[student_id], back_populates='student_parents')
    student_fee_assignments = relationship('StudentFeeAssignment', back_populates='relation', cascade='all, delete-orphan')

# FeeStructure model
class FeeStructure(db.Model):
    __tablename__ = 'FeeStructure'
    structure_id = db.Column('StructureId', db.String,
                             primary_key=True, default=lambda: str(uuid.uuid4()))
    description = db.Column('Description', db.String, nullable=False)
    total_fee = db.Column('TotalFee', db.Numeric(10, 2), nullable=False)

    # Relationships
    student_fee_assignments = relationship('StudentFeeAssignment', back_populates='fee_structure')

class PaymentHistory(db.Model):
    __tablename__ = 'PaymentHistory'
    history_id = db.Column('HistoryId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = db.Column('ParentId', db.String, nullable=False)
    timestamp = db.Column('Timestamp', db.DateTime, nullable=False)
    invoice_id = db.Column('InvoiceId', db.String, db.ForeignKey('Invoice.InvoiceId', ondelete='CASCADE'), nullable=False)
    receipt_id = db.Column('ReceiptId', db.String, db.ForeignKey('Receipt.ReceiptId', ondelete='CASCADE'), nullable=False)

    # Relationships
    invoice = db.relationship('Invoice', back_populates='payment_histories', foreign_keys=[invoice_id])
    receipt = db.relationship('Receipt', back_populates='payment_histories', foreign_keys=[receipt_id])

# Invoice model
class Invoice(db.Model):
    __tablename__ = 'Invoice'
    invoice_id = db.Column('InvoiceId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fee_record_id = db.Column('FeeRecordId', db.String, db.ForeignKey('FeeRecord.FeeRecordId', ondelete='CASCADE'), nullable=False)
    invoice_date = db.Column('InvoiceDate', db.Date, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    total_amount = db.Column('TotalAmount', db.Numeric(10, 2), nullable=False)
    late_fee_amount = db.Column('LateFeeAmount', db.Numeric(10, 2))
    discount_amount = db.Column('DiscountAmount', db.Numeric(10, 2))

    # Relationships
    receipts = db.relationship('Receipt', back_populates='invoice')
    payment_histories = db.relationship('PaymentHistory', back_populates='invoice', foreign_keys=[PaymentHistory.invoice_id])

    # Relationship to FeeRecord
    fee_record = db.relationship('FeeRecord', back_populates='invoice', uselist=False, overlaps="invoices")

# PaymentStatus model
class PaymentStatus(db.Model):
    __tablename__ = 'PaymentStatus'
    status_id = db.Column('StatusId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status_name = db.Column('StatusName', db.String, nullable=False)

    # Relationships
    fee_records = db.relationship('FeeRecord', back_populates='payment_status', cascade='all, delete-orphan')


# Class model
class Class(db.Model):
    __tablename__ = 'Class'
    class_id = db.Column('ClassId', db.String, primary_key=True,
                         default=lambda: str(uuid.uuid4()))
    class_name = db.Column('ClassName', db.String, nullable=False)
    description = db.Column('Description', db.String)

    # Relationships
    assignments = relationship('ClassAssignment', back_populates='class_')


# ClassAssignment model
class ClassAssignment(db.Model):
    __tablename__ = 'ClassAssignment'
    assignment_id = db.Column(
        'AssignmentId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column('ClassId', db.String, ForeignKey(
        'Class.ClassId', ondelete='CASCADE'))
    teacher_id = db.Column('TeacherId', db.String,
                           ForeignKey('User.Id', ondelete='SET NULL'))
    student_id = db.Column('StudentId', db.String,
                           ForeignKey('User.Id', ondelete='SET NULL'))

    # Relationships
    class_ = relationship('Class', back_populates='assignments')
    teacher = relationship('User', foreign_keys=[teacher_id], back_populates='class_assignments_as_teacher')
    student = relationship('User', foreign_keys=[student_id], back_populates='class_assignments_as_student')


# Receipt model
class Receipt(db.Model):
    __tablename__ = 'Receipt'
    receipt_id = db.Column('ReceiptId', db.String,
                           primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column('InvoiceId', db.String, ForeignKey(
        'Invoice.InvoiceId', ondelete='SET NULL'))
    amount_paid = db.Column('AmountPaid', db.Numeric(10, 2), nullable=False)
    payment_date = db.Column('PaymentDate', db.Date,
                             default=db.func.current_date())
    payment_method = db.Column('PaymentMethod', db.String)

    # Relationships
    invoice = relationship('Invoice', back_populates='receipts')
    payment_histories = db.relationship('PaymentHistory', back_populates='receipt', foreign_keys='PaymentHistory.receipt_id')

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
    relation_id = db.Column('RelationId', db.String, ForeignKey('ParentStudentRelation.RelationId', ondelete='CASCADE'))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='SET NULL'))

    # Relationships
    fee_structure = relationship('FeeStructure', back_populates='student_fee_assignments')
    fee_record = relationship('FeeRecord', back_populates='fee_assignment', uselist=False)
    relation = relationship('ParentStudentRelation', back_populates='student_fee_assignments')

# Fee record model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_record_id = db.Column('FeeRecordId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fee_assignment_id = db.Column('FeeAssignmentId', db.String, db.ForeignKey('StudentFeeAssignment.FeeAssignmentId', ondelete='CASCADE'), nullable=False)
    status_id = db.Column('StatusId', db.String, db.ForeignKey('PaymentStatus.StatusId', ondelete='SET NULL'), nullable=False)
    amount_due = db.Column('AmountDue', db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column('PaidAmount', db.Numeric(10, 2), default=0.00)
    due_date = db.Column('DueDate', db.Date, nullable=False)

    # Relationships
    payment_status = db.relationship('PaymentStatus', back_populates='fee_records')
    fee_assignment = db.relationship('StudentFeeAssignment', back_populates='fee_record', uselist=False)
    invoices = db.relationship('Invoice', back_populates='fee_record', cascade='all, delete-orphan')

    # Relationship to Invoice
    invoice = db.relationship('Invoice', back_populates='fee_record', uselist=False, overlaps="invoices")
class Message(db.Model):
    __tablename__ = 'Message'
    message_id = db.Column('MessageId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column('Name', db.String, nullable=False)
    description = db.Column('Description', db.String, nullable=False)