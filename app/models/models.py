from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid

# Role model
class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('RoleId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_name = db.Column('RoleName', db.String, nullable=False)

    # Relationships
    users = relationship('User', back_populates='role')

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column('Id', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    password = db.Column('Password', db.String, nullable=True)
    role_id = db.Column('RoleId', db.String, ForeignKey('Role.RoleId', ondelete='SET NULL'))
    email = db.Column('Email', db.String, nullable=False)
    first_name = db.Column('FirstName', db.String, nullable=False)
    last_name = db.Column('LastName', db.String, nullable=False)
    date_of_birth = db.Column('DateOfBirth', db.Date, nullable=False)
    telegram_id = db.Column('TelegramId', db.String, nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    parent_relations = relationship('ParentStudentRelation', back_populates='parent', foreign_keys='ParentStudentRelation.parent_id')
    student_relations = relationship('ParentStudentRelation', back_populates='student', foreign_keys='ParentStudentRelation.student_id')
    student_fees = relationship('StudentFeeAssignment', back_populates='student')
    class_assignments_teacher = relationship('ClassAssignment', back_populates='teacher', foreign_keys='ClassAssignment.teacher_id')
    class_assignments_student = relationship('ClassAssignment', back_populates='student', foreign_keys='ClassAssignment.student_id')
    messages_sent = relationship('Message', back_populates='teacher', foreign_keys='Message.teacher_id')
    messages_received = relationship('Message', back_populates='student', foreign_keys='Message.student_id')
    payment_histories = relationship('PaymentHistory', back_populates='student')

# Activity model
class Activity(db.Model):
    __tablename__ = 'Activity'

    activity_id = db.Column('ActivityId', db.String, primary_key=True)
    activity_name = db.Column('ActivityName', db.String, nullable=False)
    description = db.Column('Description', db.String)
    fee = db.Column('Fee', db.Numeric(10, 2), nullable=False)
    
# Class model
class Class(db.Model):
    __tablename__ = 'Class'
    class_id = db.Column('ClassId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_name = db.Column('ClassName', db.String, nullable=False)
    description = db.Column('Description', db.String, nullable=True)

    # Relationships
    assignments = relationship('ClassAssignment', back_populates='class_')

# ClassAssignment model
class ClassAssignment(db.Model):
    __tablename__ = 'ClassAssignment'
    assignment_id = db.Column('AssignmentId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column('ClassId', db.String, ForeignKey('Class.ClassId', ondelete='CASCADE'))
    teacher_id = db.Column('TeacherId', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='SET NULL'))

    # Relationships
    class_ = relationship('Class', back_populates='assignments')
    teacher = relationship('User', back_populates='class_assignments_teacher', foreign_keys=[teacher_id])
    student = relationship('User', back_populates='class_assignments_student', foreign_keys=[student_id])

# Discounts model
class Discounts(db.Model):
    __tablename__ = 'Discounts'
    discount_id = db.Column('DiscountId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='SET NULL'))
    discount_amount = db.Column('DiscountAmount', db.Numeric(10, 2), nullable=False)
    promo_code = db.Column('PromoCode', db.String(50), nullable=True)

    # Relationships
    structure = relationship('FeeStructure', back_populates='discounts')

# FeeStructure model
class FeeStructure(db.Model):
    __tablename__ = 'FeeStructure'
    structure_id = db.Column('StructureId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    description = db.Column('Description', db.String, nullable=False)
    total_fee = db.Column('TotalFee', db.Numeric(10, 2), nullable=False)

    # Relationships
    discounts = relationship('Discounts', back_populates='structure')
    student_assignments = relationship('StudentFeeAssignment', back_populates='structure')

# StudentFeeAssignment model
class StudentFeeAssignment(db.Model):
    __tablename__ = 'StudentFeeAssignment'
    
    fee_assignment_id = db.Column('FeeAssignmentId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId', ondelete='SET NULL'))
    
    # Relationships
    student = relationship('User', back_populates='student_fees')
    structure = relationship('FeeStructure', back_populates='student_assignments')
    fee_records = relationship('FeeRecord', back_populates='assignment')

# FeeRecord model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_record_id = db.Column('FeeRecordId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fee_assignment_id = db.Column('FeeAssignmentId', db.String, ForeignKey('StudentFeeAssignment.FeeAssignmentId', ondelete='CASCADE'))
    status_id = db.Column('StatusId', db.String, ForeignKey('PaymentStatus.StatusId', ondelete='SET NULL'))
    amount_due = db.Column('AmountDue', db.Numeric(10, 2), nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    last_updated_date = db.Column('LastUpdatedDate', db.Date, nullable=False)

    # Relationships
    assignment = relationship('StudentFeeAssignment', back_populates='fee_records')
    status = relationship('PaymentStatus', back_populates='fee_records')
    invoices = relationship('Invoice', back_populates='fee_record')
    payment_histories = relationship('PaymentHistory', back_populates='fee_record')

# Invoice model continued
class Invoice(db.Model):
    __tablename__ = 'Invoice'
    invoice_id = db.Column('InvoiceId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fee_record_id = db.Column('FeeRecordId', db.String, ForeignKey('FeeRecord.FeeRecordId', ondelete='SET NULL'))
    invoice_date = db.Column('InvoiceDate', db.Date, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    total_amount = db.Column('TotalAmount', db.Numeric(10, 2), nullable=False)
    late_fee_amount = db.Column('LateFeeAmount', db.Numeric(10, 2), nullable=False, default=0.00)
    discount_amount = db.Column('DiscountAmount', db.Numeric(10, 2), nullable=False, default=0.00)
    amount_due = db.Column('AmountDue', db.Numeric(10, 2), nullable=False)

    # Relationships
    fee_record = relationship('FeeRecord', back_populates='invoices')

# ParentStudentRelation model
class ParentStudentRelation(db.Model):
    __tablename__ = 'ParentStudentRelation'
    relation_id = db.Column('RelationId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = db.Column('ParentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))

    # Relationships
    parent = relationship('User', back_populates='parent_relations', foreign_keys=[parent_id])
    student = relationship('User', back_populates='student_relations', foreign_keys=[student_id])

# PaymentHistory model
class PaymentHistory(db.Model):
    __tablename__ = 'PaymentHistory'
    history_id = db.Column('PaymentHistoryId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_date = db.Column('PaymentDate', db.DateTime, nullable=False)
    receipt_id = db.Column('ReceiptId', db.String, ForeignKey('Receipt.ReceiptId', ondelete='CASCADE'))
    amount_paid = db.Column('AmountPaid', db.Numeric(10, 2), nullable=False)
    remark = db.Column('Remark', db.String, nullable=True)
    payment_method = db.Column('PaymentMethod', db.String, nullable=False)
    fee_record_id = db.Column('FeeRecordId', db.String, ForeignKey('FeeRecord.FeeRecordId', ondelete='CASCADE'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'))

    # Relationships
    receipt = relationship('Receipt', back_populates='payment_histories')
    student = relationship('User', back_populates='payment_histories')
    fee_record = relationship('FeeRecord', back_populates='payment_histories')

# Receipt model
class Receipt(db.Model):
    __tablename__ = 'Receipt'
    receipt_id = db.Column('ReceiptId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    generated_date = db.Column('GeneratedDate', db.Date, nullable=False)

    # Relationships
    payment_histories = relationship('PaymentHistory', back_populates='receipt', cascade="all, delete-orphan")

# PaymentStatus model
class PaymentStatus(db.Model):
    __tablename__ = 'PaymentStatus'
    status_id = db.Column('StatusId', db.String, primary_key=True)
    status_name = db.Column('StatusName', db.String, nullable=False)

    # Relationships
    fee_records = relationship('FeeRecord', back_populates='status')
# Message model
class Message(db.Model):
    __tablename__ = 'Message'
    message_id = db.Column('MessageId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column('TeacherId', db.String, ForeignKey('User.Id'))
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id'))
    message_type = db.Column('MessageType', db.String, nullable=False)
    message_text = db.Column('MessageText', db.String, nullable=False)
    status = db.Column('Status', db.String, nullable=False)
    read_status = db.Column('ReadStatus', db.String, nullable=False, default='unread')
    timestamp = db.Column('Timestamp', db.DateTime, nullable=False)
    delivery_method = db.Column('DeliveryMethod', db.String, nullable=False)

    # Relationships
    teacher = db.relationship('User', back_populates='messages_sent', foreign_keys=[teacher_id], single_parent=True)
    student = db.relationship('User', back_populates='messages_received', foreign_keys=[student_id])

# MessageTemplate model
class MessageTemplate(db.Model):
    __tablename__ = 'MessageTemplate'
    message_temp_id = db.Column('TemplateId', db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = db.Column('Category', db.String, nullable=False)
    template_text = db.Column('TemplateText', db.String, nullable=False)

# Settings model
class Settings(db.Model):
    __tablename__ = 'Settings'
    setting_key = db.Column('SettingKey', db.String, primary_key=True)
    setting_value = db.Column('SettingValue', db.String, nullable=False)
    description = db.Column('Description', db.String, nullable=False)
    value_type = db.Column('ValueType', db.String, nullable=False)
    category = db.Column('Category', db.String, nullable=False)
