from . import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship

# Role model
class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('Id', db.String, primary_key=True)
    role_name = db.Column('RoleName', db.String, nullable=False)
    
    # Relationship
    users = relationship('User', back_populates='role')

# Parent model
class Parent(db.Model):
    __tablename__ = 'Parent'
    id = db.Column('Id', db.String, primary_key=True)
    name = db.Column('Name', db.String, nullable=False)
    email = db.Column('Email', db.String, nullable=False)
    phone_num = db.Column('PhoneNum', db.Integer, nullable=False)
    
    # Relationship
    students = relationship('Student', back_populates='parent', cascade="all, delete-orphan")

# Student model
class Student(db.Model):
    __tablename__ = 'Student'
    id = db.Column('Id', db.String, primary_key=True)
    first_name = db.Column('FirstName', db.String, nullable=False)
    last_name = db.Column('LastName', db.String, nullable=False)
    date_of_birth = db.Column('DateOfBirth', db.Date, nullable=False)
    parent_id = db.Column('ParentId', db.String, db.ForeignKey('Parent.Id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    parent = relationship('Parent', back_populates='students')
    fee_records = relationship('FeeRecord', back_populates='student', cascade="all, delete-orphan")

# FeeStructure model
class FeeStructure(db.Model):
    __tablename__ = 'FeeStructure'
    structure_id = db.Column('StructureId', db.String, primary_key=True)
    description = db.Column('Description', db.String, nullable=False)
    total_fee = db.Column('TotalFee', db.Numeric, nullable=False)
    
    # Relationship
    fee_records = relationship('FeeRecord', back_populates='fee_structure')

# Invoice model
class Invoice(db.Model):
    __tablename__ = 'Invoice'
    invoice_id = db.Column('InvoiceId', db.String, primary_key=True)
    invoice_date = db.Column('InvoiceDate', db.Date, nullable=False)
    total_amount = db.Column('TotalAmount', db.Numeric, nullable=False)
    created_by = db.Column('CreatedBy', db.String, db.ForeignKey('User.Id', ondelete='SET NULL'))
    
    # Relationship
    fee_records = relationship('FeeRecord', back_populates='invoice')

# FeeRecord model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_id = db.Column('FeeId', db.String, primary_key=True)
    student_id = db.Column('StudentId', db.String, db.ForeignKey('Student.Id', ondelete='CASCADE'), nullable=False)
    amount_due = db.Column('AmountDue', db.Numeric, nullable=False)
    amount_paid = db.Column('AmountPaid', db.Numeric, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    invoice_id = db.Column('InvoiceId', db.String, db.ForeignKey('Invoice.InvoiceId', ondelete='SET NULL'))
    structure_id = db.Column('StructureId', db.String, db.ForeignKey('FeeStructure.StructureId'))
    created_by = db.Column('CreatedBy', db.String, db.ForeignKey('User.Id', ondelete='SET NULL'))
    
    # Relationships
    student = relationship('Student', back_populates='fee_records')
    invoice = relationship('Invoice', back_populates='fee_records')
    fee_structure = relationship('FeeStructure', back_populates='fee_records')
    created_by_user = relationship('User', back_populates='created_fee_records')

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column('Id', db.String, primary_key=True)
    username = db.Column('Username', db.String, nullable=False)
    password = db.Column('Password', db.String, nullable=False)
    role_id = db.Column('RoleId', db.String, db.ForeignKey('Role.Id', ondelete='SET NULL'))
    email = db.Column('Email', db.String, nullable=False)

    # Relationship
    role = db.relationship('Role', back_populates='users')
    created_fee_records = relationship('FeeRecord', back_populates='created_by_user')