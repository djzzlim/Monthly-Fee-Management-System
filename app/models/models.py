from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from uuid import uuid4
from sqlalchemy import Numeric, Date, String, ForeignKey, Column
import uuid

# Role model
class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('Id', db.String, primary_key=True)
    role_name = db.Column('RoleName', db.String, nullable=False)
    
    # Relationship
    users = relationship('User', back_populates='role')


# User model
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column('Id', db.String, primary_key=True, default=lambda: str(uuid4()))
    password = db.Column('Password', db.String, nullable=True)
    role_id = db.Column('RoleId', db.String, ForeignKey('Role.Id', ondelete='SET NULL'))
    email = db.Column('Email', db.String, nullable=False)
    first_name = db.Column('FirstName', db.String, nullable=False)
    last_name = db.Column('LastName', db.String, nullable=False)
    date_of_birth = db.Column('DateOfBirth', db.Date, nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    created_fee_records = db.relationship('FeeRecord', 
                                          foreign_keys='FeeRecord.created_by',  # Referencing FeeRecord.created_by
                                          backref='creator')
    invoices = relationship('Invoice', back_populates='created_by_user')
    parent_students = relationship('ParentStudent', 
                                   foreign_keys='[ParentStudent.parent_id]', 
                                   back_populates='parent', 
                                   cascade="all, delete-orphan")
    student_parents = relationship('ParentStudent', 
                                   foreign_keys='[ParentStudent.student_id]', 
                                   back_populates='student', 
                                   cascade="all, delete-orphan")


# ParentStudent association table
class ParentStudent(db.Model):
    __tablename__ = 'ParentStudent'
    parent_id = db.Column('ParentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), primary_key=True)
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), primary_key=True)

    # Relationships
    parent = relationship('User', foreign_keys=[parent_id], back_populates='parent_students')
    student = relationship('User', foreign_keys=[student_id], back_populates='student_parents')


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
    created_by = db.Column('CreatedBy', db.String, ForeignKey('User.Id', ondelete='SET NULL'))
    
    # Relationships
    fee_records = relationship('FeeRecord', back_populates='invoice')
    created_by_user = relationship('User', back_populates='invoices')


# FeeRecord model
class FeeRecord(db.Model):
    __tablename__ = 'FeeRecord'
    fee_id = db.Column('FeeId', db.String, primary_key=True)
    student_id = db.Column('StudentId', db.String, ForeignKey('User.Id', ondelete='CASCADE'), nullable=False)
    amount_due = db.Column('AmountDue', db.Numeric, nullable=False)
    amount_paid = db.Column('AmountPaid', db.Numeric, nullable=False)
    due_date = db.Column('DueDate', db.Date, nullable=False)
    invoice_id = db.Column('InvoiceId', db.String, ForeignKey('Invoice.InvoiceId', ondelete='SET NULL'))
    structure_id = db.Column('StructureId', db.String, ForeignKey('FeeStructure.StructureId'))
    created_by = db.Column('CreatedBy', db.String, ForeignKey('User.Id', ondelete='SET NULL'))  # This links back to User
    
    # Relationships
    invoice = relationship('Invoice', back_populates='fee_records')
    fee_structure = relationship('FeeStructure', back_populates='fee_records')
    
    # Specify the foreign key for the relationship with User
    created_by_user = relationship('User', back_populates='created_fee_records', foreign_keys=[created_by])  # Explicit foreign key
