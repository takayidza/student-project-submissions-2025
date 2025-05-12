from server import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    home_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)


class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    
    contact_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    vehicle_id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), nullable=False, unique=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(30), nullable=True)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    # Relationships
    incidents = db.relationship('Incident', backref='vehicle', lazy=True)
    device_associations = db.relationship('DeviceAssociation', backref='vehicle', lazy=True)

class DeviceAssociation(db.Model):
    __tablename__ = 'device_associations'
    
    association_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    device_serial = db.Column(db.String(100), nullable=False, unique=True)
    installation_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_maintenance = db.Column(db.DateTime, nullable=True)

class Responder(db.Model):
    __tablename__ = 'responders'
    
    responder_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # e.g., Ambulance, Police, Fire
    incident_type = db.Column(db.String(50), nullable=False)  # e.g., Medical, Fire, Crime
    contact_number = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    city = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    province = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    # Relationships
    incident = db.relationship('Incident', backref='responders', lazy=True)

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    incident_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device_associations.association_id'), nullable=False)
    latitude = db.Column(db.Numeric(10, 6), nullable=False)
    longitude = db.Column(db.Numeric(10, 6), nullable=False)
    incident_time = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    is_automated_alert = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Open')
    resolution_time = db.Column(db.DateTime, nullable=True)
    responder_id = db.Column(db.Integer, db.ForeignKey('responders.responder_id'), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    
   



# Association table for incidents and responders
incident_responders = db.Table('incident_responders',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.incident_id'), primary_key=True),
    db.Column('responder_id', db.Integer, db.ForeignKey('responders.responder_id'), primary_key=True),
    db.Column('dispatch_time', db.DateTime, default=datetime.utcnow),
    db.Column('arrival_time', db.DateTime, nullable=True),
    db.Column('status', db.String(20), default='Dispatched')
)