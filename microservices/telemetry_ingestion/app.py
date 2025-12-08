"""
Telemetry Ingestion Service - Streaming simulator and CSV import
Port: 5006
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
import logging
import random
import threading
import time
import csv
import io

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.models import db, Vehicle, Telemetry, MaintenanceFlag

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('TelemetryService')

app = Flask(__name__)
CORS(app)

# Database configuration
db_path = os.path.join(project_root, 'database', 'neuroride_guardian.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Simulator state
simulator_running = False
simulator_thread = None

# Simulator configuration
SIMULATOR_CONFIG = {
    'interval_seconds': 100,  # Send telemetry every 5 seconds
    'batch_size': 3,        # Number of vehicles to simulate per batch
    'variation_range': 0.1  # 10% variation in values
}

def generate_realistic_telemetry(vehicle):
    """
    Generate realistic telemetry data with some randomness
    Simulates degradation over time
    """
    # Base values with some randomness
    telemetry = {
        'vehicle_id': vehicle.vehicle_id,
        'timestamp': datetime.utcnow(),
        'mileage': vehicle.mileage + random.randint(0, 50),
        'engine_load': round(random.uniform(0.3, 0.9), 2),
        'oil_quality': round(random.uniform(2.0, 9.0), 1),
        'battery_percent': round(random.uniform(45.0, 100.0), 1),
        'brake_condition': random.choice(['Good', 'Good', 'Good', 'Warning', 'Poor']),
        'brake_temp': round(random.uniform(60.0, 120.0), 1),
        'tire_pressure': round(random.uniform(26.0, 35.0), 1),
        'fuel_consumption': round(random.uniform(6.0, 15.0), 1)
    }
    
    # Simulate degradation for some vehicles (30% chance)
    if random.random() < 0.3:
        telemetry['oil_quality'] = round(random.uniform(1.5, 4.0), 1)
        telemetry['battery_percent'] = round(random.uniform(40.0, 65.0), 1)
        telemetry['brake_condition'] = random.choice(['Warning', 'Poor'])
    
    return telemetry

def check_and_flag_maintenance(telemetry_data):
    """
    Check if telemetry indicates maintenance is needed
    Creates MaintenanceFlag if needed
    """
    vehicle_id = telemetry_data['vehicle_id']
    
    # Check if already flagged
    existing_flag = MaintenanceFlag.query.filter_by(
        vehicle_id=vehicle_id,
        is_scheduled=False
    ).first()
    
    if existing_flag:
        return False  # Already flagged
    
    # Determine if maintenance is needed
    risk_factors = []
    severity_score = 0
    
    # Oil quality check
    if telemetry_data['oil_quality'] < 3.0:
        risk_factors.append('Critical oil quality')
        severity_score += 40
    elif telemetry_data['oil_quality'] < 5.0:
        risk_factors.append('Low oil quality')
        severity_score += 20
    
    # Battery check
    if telemetry_data['battery_percent'] < 50:
        risk_factors.append('Low battery')
        severity_score += 30
    elif telemetry_data['battery_percent'] < 70:
        risk_factors.append('Battery needs attention')
        severity_score += 15
    
    # Brake condition check
    if telemetry_data['brake_condition'] == 'Poor':
        risk_factors.append('Poor brake condition')
        severity_score += 35
    elif telemetry_data['brake_condition'] == 'Warning':
        risk_factors.append('Brake warning')
        severity_score += 20
    
    # Tire pressure check
    if telemetry_data['tire_pressure'] < 28:
        risk_factors.append('Very low tire pressure')
        severity_score += 25
    elif telemetry_data['tire_pressure'] < 30:
        risk_factors.append('Low tire pressure')
        severity_score += 10
    
    # Create flag if severity is significant
    if severity_score >= 40:  # Medium severity or higher
        flag = MaintenanceFlag(
            vehicle_id=vehicle_id,
            maintenance_required=True,
            confidence=0.75 + (severity_score / 400),  # 0.75 to 1.0
            risk_factors=risk_factors,
            severity_score=severity_score,
            is_scheduled=False
        )
        db.session.add(flag)
        logger.info(f"🚩 Flagged {vehicle_id} for maintenance (severity: {severity_score})")
        return True
    
    return False

def streaming_simulator():
    """
    Background thread that simulates streaming telemetry data
    Mimics MQTT/Kafka streaming
    """
    global simulator_running
    
    logger.info("🔄 Streaming simulator started")
    
    while simulator_running:
        try:
            with app.app_context():
                # Get random vehicles to simulate
                vehicles = Vehicle.query.limit(SIMULATOR_CONFIG['batch_size']).all()
                
                for vehicle in vehicles:
                    # Generate telemetry
                    telemetry_data = generate_realistic_telemetry(vehicle)
                    
                    # Save to database
                    telemetry = Telemetry(**telemetry_data)
                    db.session.add(telemetry)
                    
                    # Check if maintenance flag needed
                    check_and_flag_maintenance(telemetry_data)
                    
                    logger.info(f"📊 Telemetry ingested for {vehicle.vehicle_id}")
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error in simulator: {str(e)}")
            db.session.rollback()
        
        # Wait before next batch
        time.sleep(SIMULATOR_CONFIG['interval_seconds'])
    
    logger.info("⏹️ Streaming simulator stopped")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'telemetry_ingestion_service',
        'version': '1.0.0',
        'simulator_running': simulator_running
    })

@app.route('/api/ingest_telemetry', methods=['POST'])
def ingest_telemetry():
    """
    Ingest single telemetry record
    Body: {
        "vehicle_id": "V123",
        "timestamp": "2025-12-01T10:00:00Z",
        "mileage": 52300,
        "engine_load": 0.62,
        "oil_quality": 2.4,
        "battery_percent": 48,
        "brake_condition": "Warning",
        ...
    }
    """
    try:
        data = request.json
        
        if not data or 'vehicle_id' not in data:
            return jsonify({'error': 'vehicle_id is required'}), 400
        
        # Validate vehicle exists
        vehicle = Vehicle.query.get(data['vehicle_id'])
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Parse timestamp
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        else:
            data['timestamp'] = datetime.utcnow()
        
        # Create telemetry record
        telemetry = Telemetry(**data)
        db.session.add(telemetry)
        
        # Check for maintenance flag
        flagged = check_and_flag_maintenance(data)
        
        db.session.commit()
        
        logger.info(f"✅ Telemetry ingested for {data['vehicle_id']}")
        
        return jsonify({
            'success': True,
            'vehicle_id': data['vehicle_id'],
            'flagged_for_maintenance': flagged,
            'timestamp': telemetry.timestamp.isoformat()
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error ingesting telemetry: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import_csv', methods=['POST'])
def import_csv():
    """
    Import historical telemetry data from CSV
    Expects CSV with columns: vehicle_id, timestamp, mileage, engine_load, oil_quality, etc.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        flagged_count = 0
        errors = []
        
        for row in csv_reader:
            try:
                # Validate vehicle exists
                vehicle_id = row.get('vehicle_id')
                if not vehicle_id:
                    continue
                
                vehicle = Vehicle.query.get(vehicle_id)
                if not vehicle:
                    errors.append(f"Vehicle {vehicle_id} not found")
                    continue
                
                # Parse data
                telemetry_data = {
                    'vehicle_id': vehicle_id,
                    'timestamp': datetime.fromisoformat(row.get('timestamp', datetime.utcnow().isoformat())),
                    'mileage': int(row.get('mileage', 0)),
                    'engine_load': float(row.get('engine_load', 0)),
                    'oil_quality': float(row.get('oil_quality', 5.0)),
                    'battery_percent': float(row.get('battery_percent', 75.0)),
                    'brake_condition': row.get('brake_condition', 'Good'),
                    'brake_temp': float(row.get('brake_temp', 80.0)),
                    'tire_pressure': float(row.get('tire_pressure', 32.0)),
                    'fuel_consumption': float(row.get('fuel_consumption', 10.0))
                }
                
                # Create telemetry record
                telemetry = Telemetry(**telemetry_data)
                db.session.add(telemetry)
                
                # Check for maintenance flag
                if check_and_flag_maintenance(telemetry_data):
                    flagged_count += 1
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row error: {str(e)}")
        
        db.session.commit()
        
        logger.info(f"✅ CSV import complete: {imported_count} records, {flagged_count} flagged")
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'flagged_count': flagged_count,
            'errors': errors[:10]  # Return first 10 errors
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error importing CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulator/start', methods=['GET', 'POST'])
def start_simulator():
    """Start the streaming telemetry simulator"""
    global simulator_running, simulator_thread
    
    if simulator_running:
        return jsonify({
            'success': False,
            'message': 'Simulator is already running'
        }), 400
    
    simulator_running = True
    simulator_thread = threading.Thread(target=streaming_simulator, daemon=True)
    simulator_thread.start()
    
    logger.info("▶️ Simulator started")
    
    return jsonify({
        'success': True,
        'message': 'Streaming simulator started',
        'config': SIMULATOR_CONFIG
    })

@app.route('/api/simulator/stop', methods=['GET', 'POST'])
def stop_simulator():
    """Stop the streaming telemetry simulator"""
    global simulator_running
    
    if not simulator_running:
        return jsonify({
            'success': False,
            'message': 'Simulator is not running'
        }), 400
    
    simulator_running = False
    
    logger.info("⏹️ Simulator stopped")
    
    return jsonify({
        'success': True,
        'message': 'Streaming simulator stopped'
    })

@app.route('/api/simulator/status', methods=['GET'])
def simulator_status():
    """Get simulator status"""
    return jsonify({
        'running': simulator_running,
        'config': SIMULATOR_CONFIG,
        'telemetry_count': Telemetry.query.count(),
        'flagged_vehicles': MaintenanceFlag.query.filter_by(is_scheduled=False).count()
    })

@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    """
    Get telemetry records with optional filtering
    Query params:
    - vehicle_id: Filter by vehicle ID
    - limit: Number of records to return (default: 50)
    """
    try:
        vehicle_id = request.args.get('vehicle_id')
        limit = int(request.args.get('limit', 50))
        
        query = Telemetry.query
        
        if vehicle_id:
            query = query.filter_by(vehicle_id=vehicle_id)
        
        telemetry = query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'telemetry': [t.to_dict() for t in telemetry],
            'count': len(telemetry)
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting telemetry: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Telemetry Ingestion Service on port 5006...")
    app.run(host='0.0.0.0', port=5006, debug=True)
