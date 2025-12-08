"""
Database models for NeuroRide Guardian Scheduling Service
SQLAlchemy ORM models for all entities
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

db = SQLAlchemy()

class Vehicle(db.Model):
    """Extended vehicle model with owner and service information"""
    __tablename__ = 'vehicles'
    
    vehicle_id = db.Column(db.String(50), primary_key=True)
    vin = db.Column(db.String(17), unique=True, nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_contact = db.Column(db.String(20), nullable=False)
    owner_email = db.Column(db.String(100))
    mileage = db.Column(db.Integer, default=0)
    last_service_date = db.Column(db.DateTime)
    customer_type = db.Column(db.String(20), default='standard')  # standard, premium, fleet
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    telemetry = db.relationship('Telemetry', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'vin': self.vin,
            'model': self.model,
            'year': self.year,
            'owner_name': self.owner_name,
            'owner_contact': self.owner_contact,
            'owner_email': self.owner_email,
            'mileage': self.mileage,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'customer_type': self.customer_type
        }


class Telemetry(db.Model):
    """Real-time and historical telemetry data"""
    __tablename__ = 'telemetry'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(50), db.ForeignKey('vehicles.vehicle_id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    mileage = db.Column(db.Integer)
    engine_load = db.Column(db.Float)  # 0.0 to 1.0
    oil_quality = db.Column(db.Float)  # 0 to 10 scale
    battery_percent = db.Column(db.Float)  # 0 to 100
    brake_condition = db.Column(db.String(20))  # Good, Warning, Poor
    brake_temp = db.Column(db.Float)  # Celsius
    tire_pressure = db.Column(db.Float)  # PSI
    fuel_consumption = db.Column(db.Float)  # L/100km
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_vehicle_timestamp', 'vehicle_id', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'timestamp': self.timestamp.isoformat(),
            'mileage': self.mileage,
            'engine_load': self.engine_load,
            'oil_quality': self.oil_quality,
            'battery_percent': self.battery_percent,
            'brake_condition': self.brake_condition,
            'brake_temp': self.brake_temp,
            'tire_pressure': self.tire_pressure,
            'fuel_consumption': self.fuel_consumption
        }


class ServiceCenter(db.Model):
    """Service center locations and capacity"""
    __tablename__ = 'service_centers'
    
    center_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    capacity_bays = db.Column(db.Integer, nullable=False, default=10)
    operating_hours_start = db.Column(db.String(5), default='08:00')  # HH:MM
    operating_hours_end = db.Column(db.String(5), default='18:00')
    contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    technicians = db.relationship('Technician', backref='service_center', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='service_center', lazy='dynamic')
    
    def to_dict(self):
        return {
            'center_id': self.center_id,
            'name': self.name,
            'region': self.region,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capacity_bays': self.capacity_bays,
            'operating_hours': f"{self.operating_hours_start}-{self.operating_hours_end}",
            'contact_phone': self.contact_phone,
            'is_active': self.is_active
        }


class Technician(db.Model):
    """Technician availability and skills"""
    __tablename__ = 'technicians'
    
    tech_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skill_level = db.Column(db.String(20), nullable=False)  # junior, senior, expert
    center_id = db.Column(db.String(50), db.ForeignKey('service_centers.center_id'), nullable=False, index=True)
    specialization = db.Column(db.String(100))  # engine, brakes, electrical, general
    is_available = db.Column(db.Boolean, default=True)
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='technician', lazy='dynamic')
    
    def to_dict(self):
        return {
            'tech_id': self.tech_id,
            'name': self.name,
            'skill_level': self.skill_level,
            'center_id': self.center_id,
            'specialization': self.specialization,
            'is_available': self.is_available,
            'contact_phone': self.contact_phone
        }


class Booking(db.Model):
    """Service appointment bookings"""
    __tablename__ = 'bookings'
    
    booking_id = db.Column(db.String(50), primary_key=True)
    vehicle_id = db.Column(db.String(50), db.ForeignKey('vehicles.vehicle_id'), nullable=False, index=True)
    center_id = db.Column(db.String(50), db.ForeignKey('service_centers.center_id'), nullable=False, index=True)
    tech_id = db.Column(db.String(50), db.ForeignKey('technicians.tech_id'), index=True)
    
    slot_start = db.Column(db.DateTime, nullable=False, index=True)
    slot_end = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(20), nullable=False, default='provisional', index=True)  
    # provisional, confirmed, in_progress, completed, cancelled
    
    priority_score = db.Column(db.Float, default=0.0)
    severity_level = db.Column(db.String(20))  # low, medium, high, critical
    service_type = db.Column(db.String(50))  # oil_change, brake_service, general_inspection, etc.
    
    estimated_duration_minutes = db.Column(db.Integer, default=60)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Composite index for slot queries
    __table_args__ = (
        Index('idx_center_slot', 'center_id', 'slot_start', 'status'),
    )
    
    def to_dict(self):
        return {
            'booking_id': self.booking_id,
            'vehicle_id': self.vehicle_id,
            'center_id': self.center_id,
            'tech_id': self.tech_id,
            'slot_start': self.slot_start.isoformat(),
            'slot_end': self.slot_end.isoformat(),
            'status': self.status,
            'priority_score': self.priority_score,
            'severity_level': self.severity_level,
            'service_type': self.service_type,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class Forecast(db.Model):
    """Regional demand forecasting"""
    __tablename__ = 'forecasts'
    
    forecast_id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(50), nullable=False, index=True)
    window_start = db.Column(db.DateTime, nullable=False, index=True)
    window_end = db.Column(db.DateTime, nullable=False)
    estimated_requests = db.Column(db.Integer, nullable=False)
    confidence_level = db.Column(db.Float)  # 0.0 to 1.0
    capacity_utilization = db.Column(db.Float)  # percentage
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite index
    __table_args__ = (
        Index('idx_region_window', 'region', 'window_start'),
    )
    
    def to_dict(self):
        return {
            'forecast_id': self.forecast_id,
            'region': self.region,
            'window_start': self.window_start.isoformat(),
            'window_end': self.window_end.isoformat(),
            'estimated_requests': self.estimated_requests,
            'confidence_level': self.confidence_level,
            'capacity_utilization': self.capacity_utilization,
            'generated_at': self.generated_at.isoformat()
        }


class Notification(db.Model):
    """Customer notification logs"""
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(50), db.ForeignKey('bookings.booking_id'), index=True)
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_contact = db.Column(db.String(20), nullable=False)
    recipient_email = db.Column(db.String(100))
    
    notification_type = db.Column(db.String(20), nullable=False)  # sms, email, both
    message_template = db.Column(db.String(50))  # booking_confirmation, reminder, completion
    message_content = db.Column(db.Text, nullable=False)
    
    status = db.Column(db.String(20), default='sent')  # sent, failed, pending
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'booking_id': self.booking_id,
            'recipient_name': self.recipient_name,
            'recipient_contact': self.recipient_contact,
            'recipient_email': self.recipient_email,
            'notification_type': self.notification_type,
            'message_template': self.message_template,
            'status': self.status,
            'sent_at': self.sent_at.isoformat()
        }


class MaintenanceFlag(db.Model):
    """Vehicles flagged for maintenance by prediction engine"""
    __tablename__ = 'maintenance_flags'
    
    flag_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(50), db.ForeignKey('vehicles.vehicle_id'), nullable=False, index=True)
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    maintenance_required = db.Column(db.Boolean, default=True)
    confidence = db.Column(db.Float)
    risk_factors = db.Column(db.JSON)  # Store as JSON array
    
    severity_score = db.Column(db.Float)  # Calculated from risk factors
    is_scheduled = db.Column(db.Boolean, default=False, index=True)
    scheduled_booking_id = db.Column(db.String(50), db.ForeignKey('bookings.booking_id'))
    
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'flag_id': self.flag_id,
            'vehicle_id': self.vehicle_id,
            'flagged_at': self.flagged_at.isoformat(),
            'maintenance_required': self.maintenance_required,
            'confidence': self.confidence,
            'risk_factors': self.risk_factors,
            'severity_score': self.severity_score,
            'is_scheduled': self.is_scheduled,
            'scheduled_booking_id': self.scheduled_booking_id,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
