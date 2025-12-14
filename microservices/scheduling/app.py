"""
Scheduling Service - Core scheduling logic and priority scoring
Port: 5003
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
import logging
import uuid
import math
import random

# Add project root to path (go up two levels from scheduling/)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.models import db, Vehicle, ServiceCenter, Technician, Booking, MaintenanceFlag

# Configure Logging
log_file = os.path.join(project_root, 'scheduling_service.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('SchedulingService')

app = Flask(__name__)
CORS(app)

# Database configuration
db_path = os.path.join(project_root, 'database', 'neuroride_guardian.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Scheduling Configuration (can be loaded from config file)
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
    },
    'severity_multipliers': {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }
}

def calculate_priority_score(vehicle, maintenance_flag, center_id, days_waiting=0):
    """
    Calculate priority score for scheduling
    
    Formula:
    priority_score = (severity_weight * severity_factor) +
                    (customer_type_weight * customer_factor) +
                    (proximity_score * distance_factor) -
                    (wait_penalty * days_waiting)
    """
    weights = SCHEDULING_CONFIG['weights']
    
    # 1. Severity Factor (0-100)
    severity_score = maintenance_flag.severity_score if maintenance_flag else 50
    severity_factor = min(severity_score, 100)
    
    # 2. Customer Type Factor (0-30)
    customer_type = vehicle.customer_type or 'standard'
    customer_factor = SCHEDULING_CONFIG['customer_type_scores'].get(customer_type, 10)
    
    # 3. Proximity Factor (0-100) - simplified for prototype
    # In production, calculate actual distance using lat/long
    proximity_factor = 75  # Default good proximity
    
    # 4. Wait Penalty
    wait_penalty_value = days_waiting * 5  # 5 points per day waiting
    
    # Calculate final score
    priority_score = (
        (weights['severity'] / 100) * severity_factor +
        (weights['customer_type'] / 100) * customer_factor +
        (weights['proximity'] / 100) * proximity_factor -
        (weights['wait_penalty'] / 100) * wait_penalty_value
    )
    
    return round(priority_score, 2)

def determine_severity_level(severity_score):
    """Determine severity level from score"""
    if severity_score >= 80:
        return 'critical'
    elif severity_score >= 60:
        return 'high'
    elif severity_score >= 40:
        return 'medium'
    else:
        return 'low'

def get_available_slots(center_id, start_date, end_date):
    """
    Get available time slots for a service center
    Returns list of available slot start times
    """
    center = ServiceCenter.query.get(center_id)
    if not center:
        return []
    
    # Get existing bookings in the date range
    existing_bookings = Booking.query.filter(
        Booking.center_id == center_id,
        Booking.slot_start >= start_date,
        Booking.slot_start < end_date,
        Booking.status.in_(['provisional', 'confirmed', 'in_progress'])
    ).all()
    
    # Generate all possible slots
    available_slots = []
    current_time = start_date
    slot_duration = timedelta(minutes=SCHEDULING_CONFIG['slot_duration_minutes'])
    
    # Parse operating hours
    try:
        start_hour, start_min = map(int, center.operating_hours_start.split(':'))
        end_hour, end_min = map(int, center.operating_hours_end.split(':'))
    except Exception as e:
        logger.error(f"Error parsing operating hours for center {center_id}: {e}")
        return []

    logger.info(f"Checking slots for {center_id} from {start_date} to {end_date}. Ops: {start_hour}:{start_min}-{end_hour}:{end_min}")

    while current_time < end_date:
        # Check if within operating hours
        # logger.info(f"Checking time: {current_time}") 
        if (current_time.hour > start_hour or 
            (current_time.hour == start_hour and current_time.minute >= start_min)) and \
           (current_time.hour < end_hour or 
            (current_time.hour == end_hour and current_time.minute < end_min)):
            
            # Count concurrent bookings at this time
            concurrent_bookings = sum(
                1 for booking in existing_bookings
                if booking.slot_start <= current_time < booking.slot_end
            )
            
            # Check if capacity available
            if concurrent_bookings < center.capacity_bays:
                available_slots.append(current_time)
            else:
                 logger.info(f"Slot {current_time} full. {concurrent_bookings}/{center.capacity_bays}")
        
        current_time += slot_duration
        
        # Move to next day if past operating hours
        if current_time.hour >= end_hour:
            # Safely move to next day using timedelta
            next_day_date = current_time.date() + timedelta(days=1)
            current_time = datetime.combine(next_day_date, datetime.min.time()).replace(
                hour=start_hour,
                minute=start_min
            )
    
    return available_slots

def find_best_technician(center_id, slot_start, slot_end, service_type=None):
    """Find best available technician for the slot"""
    technicians = Technician.query.filter_by(
        center_id=center_id,
        is_available=True
    ).all()
    
    # Check technician availability
    for tech in technicians:
        # Check if technician has conflicting bookings
        conflicting = Booking.query.filter(
            Booking.tech_id == tech.tech_id,
            Booking.slot_start < slot_end,
            Booking.slot_end > slot_start,
            Booking.status.in_(['confirmed', 'in_progress'])
        ).first()
        
        if not conflicting:
            return tech
    
    return None

def create_provisional_booking(vehicle_id, center_id, slot_start, priority_score, severity_level, service_type='general_inspection'):
    """Create a provisional booking"""
    booking_id = f"BKG-{uuid.uuid4().hex[:8].upper()}"
    slot_duration = timedelta(minutes=SCHEDULING_CONFIG['slot_duration_minutes'])
    slot_end = slot_start + slot_duration
    
    # Find available technician
    technician = find_best_technician(center_id, slot_start, slot_end, service_type)
    
    booking = Booking(
        booking_id=booking_id,
        vehicle_id=vehicle_id,
        center_id=center_id,
        tech_id=technician.tech_id if technician else None,
        slot_start=slot_start,
        slot_end=slot_end,
        status='provisional',
        priority_score=priority_score,
        severity_level=severity_level,
        service_type=service_type,
        estimated_duration_minutes=SCHEDULING_CONFIG['slot_duration_minutes'],
        created_at=datetime.utcnow()
    )
    
    db.session.add(booking)
    db.session.flush()
    return booking

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'scheduling_service',
        'version': '1.0.0'
    })

@app.route('/api/getSlots', methods=['GET'])
def get_slots():
    """
    Get available slots for a service center
    Query params: center_id, date (YYYY-MM-DD)
    """
    try:
        center_id = request.args.get('center_id')
        date_str = request.args.get('date')
        
        if not center_id or not date_str:
            return jsonify({'error': 'center_id and date are required'}), 400
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get slots for the entire day
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        slots = get_available_slots(center_id, start_date, end_date)
        
        return jsonify({
            'center_id': center_id,
            'date': date_str,
            'available_slots': [slot.isoformat() for slot in slots],
            'total_slots': len(slots)
        })
    
    except Exception as e:
        logger.error(f"Error getting slots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule_batch', methods=['POST'])
def schedule_batch():
    """
    Schedule multiple vehicles for maintenance
    Body: {
        "vehicles": ["V001", "V002"],
        "preferred_date_range": {"start": "2025-12-07", "end": "2025-12-14"}
    }
    """
    try:
        data = request.json
        vehicle_ids = data.get('vehicles', [])
        date_range = data.get('preferred_date_range', {})
        
        if not vehicle_ids:
            return jsonify({'error': 'No vehicles provided'}), 400
        
        # Parse date range
        start_date = datetime.strptime(date_range.get('start', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        end_date = datetime.strptime(date_range.get('end', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')), '%Y-%m-%d')
        
        scheduled_bookings = []
        failed_vehicles = []
        
        for vehicle_id in vehicle_ids:
            try:
                # Get vehicle and maintenance flag
                vehicle = Vehicle.query.get(vehicle_id)
                if not vehicle:
                    failed_vehicles.append({'vehicle_id': vehicle_id, 'reason': 'Vehicle not found'})
                    continue
                
                maintenance_flag = MaintenanceFlag.query.filter_by(
                    vehicle_id=vehicle_id,
                    is_scheduled=False
                ).order_by(MaintenanceFlag.flagged_at.desc()).first()
                
                if not maintenance_flag:
                    failed_vehicles.append({'vehicle_id': vehicle_id, 'reason': 'No maintenance flag found'})
                    continue
                
                # Calculate days waiting
                days_waiting = (datetime.utcnow() - maintenance_flag.flagged_at).days
                
                # Find nearest service center (simplified - use first available)
                centers = ServiceCenter.query.filter_by(is_active=True).all()
                random.shuffle(centers)
                
                if not centers:
                   failed_vehicles.append({'vehicle_id': vehicle_id, 'reason': 'No active service centers found in database'})
                   continue
                
                booking_created = False
                for center in centers:
                    # Get available slots
                    slots = get_available_slots(center.center_id, start_date, end_date)
                    
                    if slots:
                        # Calculate priority score
                        priority_score = calculate_priority_score(
                            vehicle, maintenance_flag, center.center_id, days_waiting
                        )
                        
                        severity_level = determine_severity_level(maintenance_flag.severity_score)
                        
                        # Create provisional booking
                        booking = create_provisional_booking(
                            vehicle_id=vehicle_id,
                            center_id=center.center_id,
                            slot_start=slots[0],  # Use first available slot
                            priority_score=priority_score,
                            severity_level=severity_level
                        )
                        
                        # Update maintenance flag
                        maintenance_flag.is_scheduled = True
                        maintenance_flag.scheduled_booking_id = booking.booking_id
                        
                        scheduled_bookings.append(booking.to_dict())
                        booking_created = True
                        break
                
                if not booking_created:
                    failed_vehicles.append({'vehicle_id': vehicle_id, 'reason': 'No available slots'})
            
            except Exception as e:
                logger.error(f"Error scheduling vehicle {vehicle_id}: {str(e)}")
                failed_vehicles.append({'vehicle_id': vehicle_id, 'reason': str(e)})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scheduled_count': len(scheduled_bookings),
            'failed_count': len(failed_vehicles),
            'bookings': scheduled_bookings,
            'failed_vehicles': failed_vehicles
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in batch scheduling: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/confirmBooking', methods=['POST'])
def confirm_booking():
    """
    Confirm a provisional booking
    Body: {
        "booking_id": "BKG-001",
        "customer_contact": {"name": "Rahul", "phone": "9000000000"}
    }
    """
    try:
        data = request.json
        booking_id = data.get('booking_id')
        
        if not booking_id:
            return jsonify({'error': 'booking_id is required'}), 400
        
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.status != 'provisional':
            return jsonify({'error': f'Booking is already {booking.status}'}), 400
        
        # Update booking status
        booking.status = 'confirmed'
        booking.confirmed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Booking {booking_id} confirmed")
        
        return jsonify({
            'success': True,
            'booking': booking.to_dict(),
            'message': 'Booking confirmed successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings with optional filters"""
    try:
        status = request.args.get('status')
        center_id = request.args.get('center_id')
        vehicle_id = request.args.get('vehicle_id')
        
        query = Booking.query
        
        if status:
            query = query.filter_by(status=status)
        if center_id:
            query = query.filter_by(center_id=center_id)
        if vehicle_id:
            query = query.filter_by(vehicle_id=vehicle_id)
        
        bookings = query.order_by(Booking.slot_start.desc()).limit(100).all()
        
        return jsonify({
            'bookings': [b.to_dict() for b in bookings],
            'count': len(bookings)
        })
    
    except Exception as e:
        logger.error(f"Error getting bookings: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Scheduling Service on port 5003...")
    app.run(host='0.0.0.0', port=5003, debug=True)
