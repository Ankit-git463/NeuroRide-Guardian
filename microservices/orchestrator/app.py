"""
Orchestrator Service - Workflow coordination and automation
Port: 5005
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
import logging
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.models import db, MaintenanceFlag, Booking, Notification

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('OrchestratorService')

app = Flask(__name__)
CORS(app)

# Database configuration
db_path = os.path.join(project_root, 'database', 'neuroride_guardian.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Service URLs
SERVICES = {
    'core_engine': 'http://localhost:5001',
    'scheduling': 'http://localhost:5003',
    'forecasting': 'http://localhost:5004',
    'telemetry': 'http://localhost:5006'
}

def send_notification(booking, notification_type='booking_confirmation'):
    """
    Send mocked notification (SMS/Email)
    Logs to console and database
    """
    try:
        # Get vehicle and owner info
        vehicle = booking.vehicle
        
        # Create notification message
        if notification_type == 'booking_confirmation':
            message = f"""
Dear {vehicle.owner_name},

Your vehicle maintenance appointment has been confirmed!

Vehicle: {vehicle.model} ({vehicle.vin})
Date & Time: {booking.slot_start.strftime('%B %d, %Y at %I:%M %p')}
Service Center: {booking.service_center.name}
Location: {booking.service_center.location}
Technician: {booking.technician.name if booking.technician else 'TBA'}

Booking ID: {booking.booking_id}

Please arrive 10 minutes early. For any changes, contact us at {booking.service_center.contact_phone}.

Thank you for choosing NeuroRide Guardian!
"""
        elif notification_type == 'reminder':
            message = f"""
Reminder: Your maintenance appointment is tomorrow at {booking.slot_start.strftime('%I:%M %p')}.
Booking ID: {booking.booking_id}
"""
        else:
            message = f"Notification for booking {booking.booking_id}"
        
        # Log notification (mocked SMS/Email)
        logger.info(f"📧 NOTIFICATION SENT to {vehicle.owner_contact}")
        logger.info(f"   Type: {notification_type}")
        logger.info(f"   Message: {message[:100]}...")
        
        # Save to database
        notification = Notification(
            booking_id=booking.booking_id,
            recipient_name=vehicle.owner_name,
            recipient_contact=vehicle.owner_contact,
            recipient_email=vehicle.owner_email,
            notification_type='both',  # SMS + Email
            message_template=notification_type,
            message_content=message,
            status='sent'
        )
        db.session.add(notification)
        db.session.commit()
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending notification: {str(e)}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Check all services
    services_status = {}
    for service_name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=2)
            services_status[service_name] = 'healthy' if response.status_code == 200 else 'unhealthy'
        except:
            services_status[service_name] = 'down'
    
    return jsonify({
        'status': 'healthy',
        'service': 'orchestrator_service',
        'version': '1.0.0',
        'services': services_status
    })

@app.route('/api/orchestrate/full_cycle', methods=['POST'])
def orchestrate_full_cycle():
    """
    Run complete maintenance workflow:
    1. Generate forecasts
    2. Get flagged vehicles
    3. Schedule appointments
    4. Send notifications
    
    Body: {
        "forecast_days": 7,
        "auto_confirm": false
    }
    """
    try:
        data = request.json or {}
        forecast_days = data.get('forecast_days', 7)
        auto_confirm = data.get('auto_confirm', False)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'steps': []
        }
        
        # Step 1: Generate Forecasts
        logger.info("📊 Step 1: Generating forecasts...")
        try:
            forecast_response = requests.post(
                f"{SERVICES['forecasting']}/api/forecast/generate",
                json={'forecast_days': forecast_days},
                timeout=10
            )
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                results['steps'].append({
                    'step': 'forecast_generation',
                    'status': 'success',
                    'forecasts_generated': len(forecast_data.get('forecasts', []))
                })
                logger.info(f"✅ Generated {len(forecast_data.get('forecasts', []))} forecasts")
            else:
                results['steps'].append({
                    'step': 'forecast_generation',
                    'status': 'failed',
                    'error': 'Forecasting service error'
                })
        except Exception as e:
            results['steps'].append({
                'step': 'forecast_generation',
                'status': 'failed',
                'error': str(e)
            })
        
        # Step 2: Get flagged vehicles
        logger.info("🚩 Step 2: Getting flagged vehicles...")
        flagged_vehicles = MaintenanceFlag.query.filter_by(is_scheduled=False).all()
        vehicle_ids = [flag.vehicle_id for flag in flagged_vehicles]
        
        results['steps'].append({
            'step': 'get_flagged_vehicles',
            'status': 'success',
            'flagged_count': len(vehicle_ids)
        })
        logger.info(f"✅ Found {len(vehicle_ids)} flagged vehicles")
        
        # Step 3: Schedule appointments
        if vehicle_ids:
            logger.info("📅 Step 3: Scheduling appointments...")
            try:
                schedule_response = requests.post(
                    f"{SERVICES['scheduling']}/api/schedule_batch",
                    json={
                        'vehicles': vehicle_ids,
                        'preferred_date_range': {
                            'start': datetime.now().strftime('%Y-%m-%d'),
                            'end': (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
                        }
                    },
                    timeout=30
                )
                
                if schedule_response.status_code == 200:
                    schedule_data = schedule_response.json()
                    results['steps'].append({
                        'step': 'scheduling',
                        'status': 'success',
                        'scheduled_count': schedule_data.get('scheduled_count', 0),
                        'failed_count': schedule_data.get('failed_count', 0)
                    })
                    logger.info(f"✅ Scheduled {schedule_data.get('scheduled_count', 0)} appointments")
                    
                    # Step 4: Send notifications (if auto_confirm)
                    if auto_confirm:
                        logger.info("📧 Step 4: Sending notifications...")
                        notification_count = 0
                        
                        for booking_data in schedule_data.get('bookings', []):
                            booking = Booking.query.get(booking_data['booking_id'])
                            if booking:
                                # Confirm booking
                                booking.status = 'confirmed'
                                booking.confirmed_at = datetime.utcnow()
                                
                                # Send notification
                                if send_notification(booking):
                                    notification_count += 1
                        
                        db.session.commit()
                        
                        results['steps'].append({
                            'step': 'notifications',
                            'status': 'success',
                            'sent_count': notification_count
                        })
                        logger.info(f"✅ Sent {notification_count} notifications")
                else:
                    results['steps'].append({
                        'step': 'scheduling',
                        'status': 'failed',
                        'error': 'Scheduling service error'
                    })
            except Exception as e:
                results['steps'].append({
                    'step': 'scheduling',
                    'status': 'failed',
                    'error': str(e)
                })
        else:
            results['steps'].append({
                'step': 'scheduling',
                'status': 'skipped',
                'reason': 'No vehicles to schedule'
            })
        
        # Step 5: Process feedback to forecasting
        logger.info("🔄 Step 5: Processing feedback...")
        try:
            # Get capacity utilization from scheduling
            capacity_response = requests.get(
                f"{SERVICES['forecasting']}/api/forecast/capacity",
                timeout=5
            )
            
            if capacity_response.status_code == 200:
                capacity_data = capacity_response.json()
                
                # Send feedback for high utilization centers
                for center in capacity_data.get('capacity_forecast', []):
                    if center['utilization_percent'] > 80:
                        requests.post(
                            f"{SERVICES['forecasting']}/api/forecast/feedback",
                            json={
                                'region': center['region'],
                                'actual_demand': center['current_bookings'],
                                'capacity_utilization': center['utilization_percent'] / 100
                            },
                            timeout=5
                        )
                
                results['steps'].append({
                    'step': 'feedback_processing',
                    'status': 'success'
                })
                logger.info("✅ Feedback processed")
        except Exception as e:
            results['steps'].append({
                'step': 'feedback_processing',
                'status': 'failed',
                'error': str(e)
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"❌ Orchestration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrate/schedule_flagged', methods=['POST'])
def schedule_flagged_vehicles():
    """
    Schedule all currently flagged vehicles
    Simpler version of full cycle - just scheduling
    """
    try:
        # Get flagged vehicles
        flagged_vehicles = MaintenanceFlag.query.filter_by(is_scheduled=False).all()
        vehicle_ids = [flag.vehicle_id for flag in flagged_vehicles]
        
        if not vehicle_ids:
            return jsonify({
                'success': True,
                'message': 'No vehicles flagged for maintenance',
                'scheduled_count': 0
            })
        
        # Schedule them
        schedule_response = requests.post(
            f"{SERVICES['scheduling']}/api/schedule_batch",
            json={
                'vehicles': vehicle_ids,
                'preferred_date_range': {
                    'start': datetime.now().strftime('%Y-%m-%d'),
                    'end': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                }
            },
            timeout=30
        )
        
        if schedule_response.status_code == 200:
            schedule_data = schedule_response.json()
            return jsonify({
                'success': True,
                'scheduled_count': schedule_data.get('scheduled_count', 0),
                'failed_count': schedule_data.get('failed_count', 0),
                'bookings': schedule_data.get('bookings', [])
            })
        else:
            return jsonify({'error': 'Scheduling service error'}), 500
    
    except Exception as e:
        logger.error(f"❌ Error scheduling flagged vehicles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/send', methods=['POST'])
def send_notification_endpoint():
    """
    Send notification for a specific booking
    Body: {
        "booking_id": "BKG-XXX",
        "notification_type": "booking_confirmation"
    }
    """
    try:
        data = request.json
        booking_id = data.get('booking_id')
        notification_type = data.get('notification_type', 'booking_confirmation')
        
        if not booking_id:
            return jsonify({'error': 'booking_id is required'}), 400
        
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        success = send_notification(booking, notification_type)
        
        return jsonify({
            'success': success,
            'booking_id': booking_id,
            'notification_type': notification_type
        })
    
    except Exception as e:
        logger.error(f"❌ Error sending notification: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get all notifications with optional filters"""
    try:
        booking_id = request.args.get('booking_id')
        limit = int(request.args.get('limit', 50))
        
        query = Notification.query
        
        if booking_id:
            query = query.filter_by(booking_id=booking_id)
        
        notifications = query.order_by(Notification.sent_at.desc()).limit(limit).all()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications)
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting notifications: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Orchestrator Service on port 5005...")
    app.run(host='0.0.0.0', port=5005, debug=True)
