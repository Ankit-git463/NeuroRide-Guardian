# NeuroRide Guardian - Scheduling Service Setup

## Phase 2A Progress: Database & Scheduling Service ✅

### Completed Components

1. **Database Models** (`database/models.py`)
   - ✅ Vehicle (extended with owner info, VIN)
   - ✅ Telemetry (real-time sensor data)
   - ✅ ServiceCenter (locations, capacity)
   - ✅ Technician (skills, availability)
   - ✅ Booking (appointments with priority scoring)
   - ✅ Forecast (regional demand predictions)
   - ✅ Notification (customer communications)
   - ✅ MaintenanceFlag (flagged vehicles)

2. **Database Seed Script** (`database/seed_data.py`)
   - ✅ 5 Service Centers across Delhi NCR
   - ✅ 17 Technicians with varying skill levels
   - ✅ 50 Sample Vehicles
   - ✅ Telemetry data for 20 vehicles
   - ✅ 15 Maintenance flags

3. **Scheduling Service** (`microservices/scheduling/app.py`)
   - ✅ Priority scoring algorithm
   - ✅ Slot availability checking
   - ✅ Batch scheduling endpoint
   - ✅ Booking confirmation
   - ✅ Technician allocation

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Install Flask-SQLAlchemy for database operations
pip install Flask-SQLAlchemy==3.1.1

# Install scheduling service dependencies
cd microservices/scheduling
pip install -r requirements.txt
cd ../..
```

### Step 2: Initialize Database

```bash
# Run the seed script to create tables and populate data
python database/seed_data.py
```

Expected output:
```
============================================================
NeuroRide Guardian - Database Initialization
============================================================
🗄️  Creating database tables...
✅ Database tables created successfully!

🏢 Seeding service centers...
✅ Added 5 service centers

👨‍🔧 Seeding technicians...
✅ Added 17 technicians

🚗 Seeding vehicles...
✅ Added 50 vehicles

📊 Seeding telemetry data...
✅ Added 120 telemetry records

🚩 Seeding maintenance flags...
✅ Added 15 maintenance flags

============================================================
✅ Database initialization complete!
============================================================

📊 Summary:
  - Service Centers: 5
  - Technicians: 17
  - Vehicles: 50
  - Telemetry Records: 120
  - Maintenance Flags: 15

🚀 Ready to start services!
```

### Step 3: Test Scheduling Service

```bash
# Start the scheduling service
cd microservices/scheduling
python app.py
```

The service will start on **port 5003**.

## API Testing

### 1. Health Check
```bash
curl http://localhost:5003/health
```

### 2. Get Available Slots
```bash
curl "http://localhost:5003/api/getSlots?center_id=SC001&date=2025-12-08"
```

### 3. Schedule Batch of Vehicles
```bash
curl -X POST http://localhost:5003/api/schedule_batch \
  -H "Content-Type: application/json" \
  -d '{
    "vehicles": ["V001", "V002", "V003"],
    "preferred_date_range": {
      "start": "2025-12-08",
      "end": "2025-12-15"
    }
  }'
```

### 4. Confirm Booking
```bash
curl -X POST http://localhost:5003/api/confirmBooking \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "BKG-XXXXXXXX",
    "customer_contact": {
      "name": "Rahul",
      "phone": "9000000000"
    }
  }'
```

### 5. Get All Bookings
```bash
curl "http://localhost:5003/api/bookings?status=provisional"
```

## Priority Scoring Algorithm

The scheduling service uses a weighted priority scoring system:

```
priority_score = (severity_weight * severity_factor) +
                (customer_type_weight * customer_factor) +
                (proximity_score * distance_factor) -
                (wait_penalty * days_waiting)
```

### Default Weights (Configurable)
- **Severity Weight**: 40% (based on risk factors and maintenance urgency)
- **Customer Type Weight**: 20% (fleet > premium > standard)
- **Proximity Score**: 25% (distance to service center)
- **Wait Penalty**: 15% (penalizes longer wait times)

### Severity Levels
- **Critical**: severity_score >= 80 (immediate attention)
- **High**: severity_score >= 60 (within 2-3 days)
- **Medium**: severity_score >= 40 (within a week)
- **Low**: severity_score < 40 (routine maintenance)

## Database Schema Overview

```
vehicles
├── vehicle_id (PK)
├── vin (unique)
├── model, year
├── owner_name, owner_contact, owner_email
├── mileage, last_service_date
└── customer_type (standard/premium/fleet)

service_centers
├── center_id (PK)
├── name, region, location
├── latitude, longitude
├── capacity_bays
└── operating_hours

technicians
├── tech_id (PK)
├── name, skill_level
├── center_id (FK)
└── specialization

bookings
├── booking_id (PK)
├── vehicle_id (FK)
├── center_id (FK)
├── tech_id (FK)
├── slot_start, slot_end
├── status (provisional/confirmed/in_progress/completed)
├── priority_score
└── severity_level

maintenance_flags
├── flag_id (PK)
├── vehicle_id (FK)
├── flagged_at
├── severity_score
├── risk_factors (JSON)
└── is_scheduled
```

## Next Steps

### Phase 2B: Forecasting & Telemetry Ingestion
- [ ] Forecasting Service (Port 5004)
- [ ] Telemetry Ingestion Service (Port 5006)
- [ ] Streaming Simulator
- [ ] CSV Import Functionality

### Phase 2C: Orchestrator
- [ ] Orchestrator Service (Port 5005)
- [ ] Workflow Coordination
- [ ] Notification Service Integration

### Phase 2D: Frontend
- [ ] Admin Dashboard
- [ ] Booking Management UI
- [ ] Service Center View
- [ ] Customer Portal

## Troubleshooting

### Database File Not Found
If you see "unable to open database file":
```bash
# Ensure you're running from the project root
cd d:\EYSOLUTION\maintenance-predictor
python database/seed_data.py
```

### Port Already in Use
If port 5003 is busy:
```bash
# Find and kill the process (Windows)
netstat -ano | findstr :5003
taskkill /PID <PID> /F
```

### Import Errors
If you see module import errors:
```bash
# Ensure you're in the correct directory
cd microservices/scheduling
python app.py
```

## Configuration

The scheduling service configuration is in `microservices/scheduling/app.py`:

```python
SCHEDULING_CONFIG = {
    'weights': {
        'severity': 40,
        'customer_type': 20,
        'proximity': 25,
        'wait_penalty': 15
    },
    'slot_duration_minutes': 60,
    'customer_type_scores': {
        'fleet': 30,
        'premium': 20,
        'standard': 10
    }
}
```

You can modify these values to adjust the scheduling behavior.

## Support

For issues or questions, refer to:
- Main README: `README.md`
- Integration Plan: `SCHEDULING_INTEGRATION_PLAN.md`
- API Documentation: Coming in Phase 2D
