from app import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointment'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    clinic_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='upcoming')
    
    def __repr__(self):
        return f'<Appointment {self.id}>'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    full_name = db.Column(db.String(100))  # <-- Add this line for full name
    visit_date = db.Column(db.DateTime, nullable=False)
    doctor = db.Column(db.String(100))
    clinic = db.Column(db.String(100))
    diagnosis = db.Column(db.String(500))  # Can be nullable
    notes = db.Column(db.Text)
    hl7_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    diagnoses = db.relationship('Diagnosis', backref='medical_record', cascade="all, delete-orphan")
    medications = db.relationship('Medication', backref='medical_record', cascade="all, delete-orphan")

class Diagnosis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_record.id'), nullable=False)
    code = db.Column(db.String(20))
    description = db.Column(db.String(500))
    coding_system = db.Column(db.String(50))
    diagnosis_date = db.Column(db.DateTime)
    status = db.Column(db.String(10))

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_record.id'), nullable=False)
    name = db.Column(db.String(200))
    code = db.Column(db.String(20))
    dosage = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    route = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(100))
    form = db.Column(db.String(50))