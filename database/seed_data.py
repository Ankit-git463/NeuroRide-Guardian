"""
Database initialization and seed data script
Run this to create tables and populate with sample data
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from database.models import (
    db, Vehicle, Telemetry, ServiceCenter, Technician, 
    Booking, Forecast, Notification, MaintenanceFlag
)

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    # Use absolute path for database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neuroride_guardian.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        print("🗄️  Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")

def seed_service_centers(app):
    """Seed service centers"""
    with app.app_context():
        print("\n🏢 Seeding service centers...")
        
        centers = [
            ServiceCenter(
                center_id='SC001',
                name='NeuroRide Service Center - North Delhi',
                region='North Delhi',
                location='Sector 18, Rohini, New Delhi',
                latitude=28.7041,
                longitude=77.1025,
                capacity_bays=15,
                operating_hours_start='08:00',
                operating_hours_end='20:00',
                contact_phone='+91-11-12345678'
            ),
            ServiceCenter(
                center_id='SC002',
                name='NeuroRide Service Center - South Delhi',
                region='South Delhi',
                location='Saket, New Delhi',
                latitude=28.5244,
                longitude=77.2066,
                capacity_bays=12,
                operating_hours_start='09:00',
                operating_hours_end='19:00',
                contact_phone='+91-11-23456789'
            ),
            ServiceCenter(
                center_id='SC003',
                name='NeuroRide Service Center - Gurgaon',
                region='Gurgaon',
                location='Cyber City, Gurgaon',
                latitude=28.4595,
                longitude=77.0266,
                capacity_bays=20,
                operating_hours_start='08:00',
                operating_hours_end='21:00',
                contact_phone='+91-124-3456789'
            ),
            ServiceCenter(
                center_id='SC004',
                name='NeuroRide Service Center - Noida',
                region='Noida',
                location='Sector 62, Noida',
                latitude=28.6139,
                longitude=77.3910,
                capacity_bays=10,
                operating_hours_start='08:30',
                operating_hours_end='18:30',
                contact_phone='+91-120-4567890'
            ),
            ServiceCenter(
                center_id='SC005',
                name='NeuroRide Service Center - Faridabad',
                region='Faridabad',
                location='Sector 15, Faridabad',
                latitude=28.4089,
                longitude=77.3178,
                capacity_bays=8,
                operating_hours_start='09:00',
                operating_hours_end='18:00',
                contact_phone='+91-129-5678901'
            )
        ]
        
        for center in centers:
            db.session.add(center)
        
        db.session.commit()
        print(f"✅ Added {len(centers)} service centers")

def seed_technicians(app):
    """Seed technicians"""
    with app.app_context():
        print("\n👨‍🔧 Seeding technicians...")
        
        technicians = [
            # North Delhi (SC001)
            Technician(tech_id='T001', name='Rajesh Kumar', skill_level='expert', center_id='SC001', specialization='engine', contact_phone='+91-9876543210'),
            Technician(tech_id='T002', name='Amit Singh', skill_level='senior', center_id='SC001', specialization='brakes', contact_phone='+91-9876543211'),
            Technician(tech_id='T003', name='Priya Sharma', skill_level='senior', center_id='SC001', specialization='electrical', contact_phone='+91-9876543212'),
            Technician(tech_id='T004', name='Vikram Patel', skill_level='junior', center_id='SC001', specialization='general', contact_phone='+91-9876543213'),
            
            # South Delhi (SC002)
            Technician(tech_id='T005', name='Suresh Reddy', skill_level='expert', center_id='SC002', specialization='general', contact_phone='+91-9876543214'),
            Technician(tech_id='T006', name='Neha Gupta', skill_level='senior', center_id='SC002', specialization='engine', contact_phone='+91-9876543215'),
            Technician(tech_id='T007', name='Rahul Verma', skill_level='junior', center_id='SC002', specialization='brakes', contact_phone='+91-9876543216'),
            
            # Gurgaon (SC003)
            Technician(tech_id='T008', name='Deepak Mehta', skill_level='expert', center_id='SC003', specialization='electrical', contact_phone='+91-9876543217'),
            Technician(tech_id='T009', name='Anjali Kapoor', skill_level='expert', center_id='SC003', specialization='engine', contact_phone='+91-9876543218'),
            Technician(tech_id='T010', name='Sanjay Joshi', skill_level='senior', center_id='SC003', specialization='general', contact_phone='+91-9876543219'),
            Technician(tech_id='T011', name='Pooja Agarwal', skill_level='senior', center_id='SC003', specialization='brakes', contact_phone='+91-9876543220'),
            Technician(tech_id='T012', name='Karan Malhotra', skill_level='junior', center_id='SC003', specialization='general', contact_phone='+91-9876543221'),
            
            # Noida (SC004)
            Technician(tech_id='T013', name='Manish Saxena', skill_level='senior', center_id='SC004', specialization='engine', contact_phone='+91-9876543222'),
            Technician(tech_id='T014', name='Ritu Bansal', skill_level='senior', center_id='SC004', specialization='electrical', contact_phone='+91-9876543223'),
            Technician(tech_id='T015', name='Arjun Rao', skill_level='junior', center_id='SC004', specialization='general', contact_phone='+91-9876543224'),
            
            # Faridabad (SC005)
            Technician(tech_id='T016', name='Gaurav Sharma', skill_level='senior', center_id='SC005', specialization='general', contact_phone='+91-9876543225'),
            Technician(tech_id='T017', name='Sneha Iyer', skill_level='junior', center_id='SC005', specialization='brakes', contact_phone='+91-9876543226'),
        ]
        
        for tech in technicians:
            db.session.add(tech)
        
        db.session.commit()
        print(f"✅ Added {len(technicians)} technicians")

def seed_vehicles(app):
    """Seed sample vehicles"""
    with app.app_context():
        print("\n🚗 Seeding vehicles...")
        
        models = ['Maruti Swift', 'Hyundai Creta', 'Tata Nexon', 'Honda City', 'Mahindra Scorpio', 
                  'Toyota Innova', 'Ford EcoSport', 'Renault Duster', 'Kia Seltos', 'MG Hector']
        customer_types = ['standard', 'premium', 'fleet']
        
        vehicles = []
        for i in range(1, 51):  # 50 vehicles
            vehicle = Vehicle(
                vehicle_id=f'V{i:03d}',
                vin=f'1HGBH41JXMN{100000+i}',
                model=random.choice(models),
                year=random.randint(2015, 2024),
                owner_name=f'Customer {i}',
                owner_contact=f'+91-98765{43210+i}',
                owner_email=f'customer{i}@example.com',
                mileage=random.randint(10000, 100000),
                last_service_date=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                customer_type=random.choice(customer_types)
            )
            vehicles.append(vehicle)
            db.session.add(vehicle)
        
        db.session.commit()
        print(f"✅ Added {len(vehicles)} vehicles")

def seed_telemetry(app):
    """Seed sample telemetry data"""
    with app.app_context():
        print("\n📊 Seeding telemetry data...")
        
        vehicles = Vehicle.query.limit(20).all()  # Add telemetry for first 20 vehicles
        brake_conditions = ['Good', 'Warning', 'Poor']
        
        telemetry_count = 0
        for vehicle in vehicles:
            # Add 5-10 telemetry records per vehicle
            num_records = random.randint(5, 10)
            for j in range(num_records):
                telemetry = Telemetry(
                    vehicle_id=vehicle.vehicle_id,
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                    mileage=vehicle.mileage + random.randint(-1000, 1000),
                    engine_load=round(random.uniform(0.3, 0.9), 2),
                    oil_quality=round(random.uniform(1.0, 9.0), 1),
                    battery_percent=round(random.uniform(40.0, 100.0), 1),
                    brake_condition=random.choice(brake_conditions),
                    brake_temp=round(random.uniform(60.0, 120.0), 1),
                    tire_pressure=round(random.uniform(28.0, 35.0), 1),
                    fuel_consumption=round(random.uniform(6.0, 15.0), 1)
                )
                db.session.add(telemetry)
                telemetry_count += 1
        
        db.session.commit()
        print(f"✅ Added {telemetry_count} telemetry records")

def seed_maintenance_flags(app):
    """Seed maintenance flags for vehicles needing service"""
    with app.app_context():
        print("\n🚩 Seeding maintenance flags...")
        
        vehicles = Vehicle.query.limit(15).all()  # Flag first 15 vehicles
        
        flags = []
        for vehicle in vehicles:
            # Determine severity based on random factors
            oil_quality = random.uniform(1.0, 9.0)
            battery = random.uniform(40.0, 100.0)
            
            risk_factors = []
            severity_score = 0
            
            if oil_quality < 3.0:
                risk_factors.append('Critical oil quality')
                severity_score += 40
            elif oil_quality < 5.0:
                risk_factors.append('Low oil quality')
                severity_score += 20
            
            if battery < 50:
                risk_factors.append('Low battery')
                severity_score += 30
            elif battery < 70:
                risk_factors.append('Battery needs attention')
                severity_score += 15
            
            if random.choice([True, False]):
                risk_factors.append('High mileage since last service')
                severity_score += 25
            
            flag = MaintenanceFlag(
                vehicle_id=vehicle.vehicle_id,
                flagged_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                maintenance_required=True,
                confidence=round(random.uniform(0.65, 0.98), 2),
                risk_factors=risk_factors,
                severity_score=severity_score,
                is_scheduled=False
            )
            flags.append(flag)
            db.session.add(flag)
        
        db.session.commit()
        print(f"✅ Added {len(flags)} maintenance flags")

def main():
    """Main seed function"""
    print("=" * 60)
    print("NeuroRide Guardian - Database Initialization")
    print("=" * 60)
    
    app = create_app()
    
    # Initialize database
    init_database(app)
    
    # Seed data
    seed_service_centers(app)
    seed_technicians(app)
    seed_vehicles(app)
    seed_telemetry(app)
    seed_maintenance_flags(app)
    
    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print("\n📊 Summary:")
    with app.app_context():
        print(f"  - Service Centers: {ServiceCenter.query.count()}")
        print(f"  - Technicians: {Technician.query.count()}")
        print(f"  - Vehicles: {Vehicle.query.count()}")
        print(f"  - Telemetry Records: {Telemetry.query.count()}")
        print(f"  - Maintenance Flags: {MaintenanceFlag.query.count()}")
    print("\n🚀 Ready to start services!")

if __name__ == '__main__':
    main()
