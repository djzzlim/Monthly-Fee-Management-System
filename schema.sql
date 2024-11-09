-- Drop tables if they exist to avoid conflicts
DROP TABLE IF EXISTS Invoice;
DROP TABLE IF EXISTS FeeRecord;
DROP TABLE IF EXISTS FeeStructure;
DROP TABLE IF EXISTS Student;
DROP TABLE IF EXISTS Parent;
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Role;

-- Create Role table
CREATE TABLE Role (
    Id TEXT PRIMARY KEY,
    RoleName TEXT
);

-- Create Parent table
CREATE TABLE Parent (
    Id TEXT PRIMARY KEY,
    Name TEXT,
    Email TEXT,
    PhoneNum INTEGER
);

-- Create Student table with a foreign key reference to Parent
CREATE TABLE Student (
    Id TEXT PRIMARY KEY,
    FirstName TEXT,
    LastName TEXT,
    DateOfBirth DATE,
    ParentId TEXT,
    FOREIGN KEY (ParentId) REFERENCES Parent(Id) ON DELETE CASCADE
);

-- Create FeeStructure table
CREATE TABLE FeeStructure (
    StructureId TEXT PRIMARY KEY,
    Description TEXT,
    TotalFee DECIMAL
);

-- Create Invoice table
CREATE TABLE Invoice (
    InvoiceId TEXT PRIMARY KEY,
    InvoiceDate DATE,
    TotalAmount DECIMAL,
    CreatedBy TEXT
);

-- Create FeeRecord table with foreign key references to Student, Invoice, and FeeStructure
CREATE TABLE FeeRecord (
    FeeId TEXT PRIMARY KEY,
    StudentId TEXT,
    AmountDue DECIMAL,
    AmountPaid DECIMAL,
    DueDate DATE,
    InvoiceId TEXT,
    StructureId TEXT,
    CreatedBy TEXT,
    FOREIGN KEY (StudentId) REFERENCES Student(Id) ON DELETE CASCADE,
    FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId) ON DELETE SET NULL,
    FOREIGN KEY (StructureId) REFERENCES FeeStructure(StructureId),
    FOREIGN KEY (CreatedBy) REFERENCES User(Id) ON DELETE SET NULL
);

-- Create User table with a foreign key reference to Role
CREATE TABLE User (
    Id TEXT PRIMARY KEY,
    Username TEXT,
    Password TEXT,
    RoleId TEXT,
    Email TEXT,
    FOREIGN KEY (RoleId) REFERENCES Role(Id) ON DELETE SET NULL
);
