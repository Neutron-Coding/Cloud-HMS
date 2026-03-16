from flask_sqlalchemy import SQLAlchemy
from .database import db
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    user_role = db.Column(db.Integer, nullable=False)  # 1=Admin, 2=Doctor, 3=Patient
    admin = db.relationship('Admin', backref='user') 
    doctor = db.relationship('Doctor', backref='user') 
    patient = db.relationship('Patient', backref='user') 
    '''uselist=False, cascade='all, delete-orphan'''
    
    def get_id(self):
        return str(self.id)




class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))






class Department(db.Model, UserMixin):
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    doctors = db.relationship('Doctor', backref='department', lazy=True)





class Doctor(db.Model, UserMixin):
    __tablename__ = 'doctor'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255))
    full_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(200))
    experience = db.Column(db.Integer)
    registration_number = db.Column(db.String(50), unique=True)
    flagged = db.Column(db.Boolean, nullable=False, default=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    
    appointments = db.relationship('Appointment', backref='doctor')





class Patient(db.Model, UserMixin):
    __tablename__ = 'patient'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255))
    age = db.Column(db.Integer)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  
    blood_group = db.Column(db.String(5))
    medical_history = db.Column(db.Text)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    flagged = db.Column(db.Boolean, nullable=False, default=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)






class Appointment(db.Model, UserMixin):
    __tablename__ = 'appointment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, nullable=False, default=999) 
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Available')
    reason = db.Column('reason_for_visit', db.Text)
    
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')






class Treatment(db.Model, UserMixin):
    __tablename__ = 'treatment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), 
                            nullable=False, unique=True)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    notes = db.Column('treatment_notes', db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)