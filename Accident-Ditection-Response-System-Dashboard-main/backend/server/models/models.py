from server import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True)
    incidents = db.relationship('Incident', backref='reported_by', lazy=True)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    registration_number = db.Column(db.String(20), nullable=False, unique=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(30), nullable=True)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    incidents = db.relationship('Incident', backref='vehicle', lazy=True)
    device_associations = db.relationship('DeviceAssociation', backref='vehicle', lazy=True)

class HighRiskArea(db.Model):
    __tablename__ = 'high_risk_areas'
    
    area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(100), nullable=False)
    center_latitude = db.Column(db.Numeric(10, 6), nullable=False)
    center_longitude = db.Column(db.Numeric(10, 6), nullable=False)
    radius_km = db.Column(db.Numeric(10, 2), nullable=False)
    incident_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level = db.Column(db.String(20), nullable=False)

class IoTDevice(db.Model):
    __tablename__ = 'iot_devices'
    
    device_id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    manufacturing_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    device_associations = db.relationship('DeviceAssociation', backref='device', lazy=True)

class DeviceAssociation(db.Model):
    __tablename__ = 'device_associations'
    
    association_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('iot_devices.device_id'), nullable=False)
    installation_date = db.Column(db.DateTime, default=datetime.utcnow)
    installation_notes = db.Column(db.String(255), nullable=True)

class Location(db.Model):
    __tablename__ = 'locations'
    
    location_id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Numeric(10, 6), nullable=False)
    longitude = db.Column(db.Numeric(10, 6), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    area_name = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    is_remote_area = db.Column(db.Boolean, default=False)
    
    # Relationships
    incidents = db.relationship('Incident', backref='location', lazy=True)

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    incident_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'), nullable=False)
    incident_time = db.Column(db.DateTime, default=datetime.utcnow)
    incident_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    is_automated_alert = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Open')
    resolution_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    status_updates = db.relationship('StatusUpdate', backref='incident', lazy=True)
    emergency_services = db.relationship('EmergencyService', backref='incident', lazy=True)

class StatusUpdate(db.Model):
    __tablename__ = 'status_updates'
    
    update_id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.incident_id'), nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

class ResponseTeam(db.Model):
    __tablename__ = 'response_teams'
    
    team_id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    team_type = db.Column(db.String(50), nullable=False)
    base_location = db.Column(db.String(255), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    last_dispatch_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    personnel = db.relationship('EmergencyPersonnel', backref='team', lazy=True)
    incidents = db.relationship('Incident', secondary='team_incident', backref='response_teams')

# Association table for many-to-many relationship between teams and incidents
team_incident = db.Table('team_incident',
    db.Column('team_id', db.Integer, db.ForeignKey('response_teams.team_id'), primary_key=True),
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.incident_id'), primary_key=True),
    db.Column('dispatch_time', db.DateTime, default=datetime.utcnow)
)

class EmergencyPersonnel(db.Model):
    __tablename__ = 'emergency_personnel'
    
    personnel_id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('response_teams.team_id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, default=True)

class EmergencyService(db.Model):
    __tablename__ = 'emergency_services'
    
    service_id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.incident_id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    provider_name = db.Column(db.String(100), nullable=False)
    dispatch_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(500), nullable=True)

# Many-to-many relationship between high risk areas and incidents
incident_high_risk_area = db.Table('incident_high_risk_area',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.incident_id'), primary_key=True),
    db.Column('area_id', db.Integer, db.ForeignKey('high_risk_areas.area_id'), primary_key=True)
)
