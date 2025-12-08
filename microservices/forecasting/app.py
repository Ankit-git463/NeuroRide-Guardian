"""
Forecasting Service - Regional demand prediction and capacity planning
Port: 5004
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
import logging
from collections import defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.models import db, Vehicle, ServiceCenter, Booking, Forecast, MaintenanceFlag, Telemetry

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('ForecastingService')

app = Flask(__name__)
CORS(app)

# Database configuration
db_path = os.path.join(project_root, 'database', 'neuroride_guardian.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Forecasting Configuration
FORECAST_CONFIG = {
    'base_multiplier': 1.2,  # Base demand multiplier
    'capacity_threshold_high': 0.9,  # 90% capacity triggers increase
    'capacity_threshold_low': 0.5,   # 50% capacity triggers decrease
    'multiplier_adjustment': 0.1,    # Adjustment per feedback cycle
    'forecast_days': 7,              # Default forecast window
    'min_historical_days': 30        # Minimum historical data for forecasting
}

def calculate_severity_from_telemetry(telemetry_records):
    """
    Calculate severity score from telemetry data
    Uses the same rules as the prediction engine
    """
    if not telemetry_records:
        return 0
    
    # Get most recent telemetry
    latest = telemetry_records[0]
    severity_score = 0
    
    # Oil quality check
    if latest.oil_quality is not None:
        if latest.oil_quality < 3.0:
            severity_score += 40
        elif latest.oil_quality < 5.0:
            severity_score += 20
    
    # Battery check
    if latest.battery_percent is not None:
        if latest.battery_percent < 50:
            severity_score += 30
        elif latest.battery_percent < 70:
            severity_score += 15
    
    # Brake condition check
    if latest.brake_condition:
        if latest.brake_condition == 'Poor':
            severity_score += 35
        elif latest.brake_condition == 'Warning':
            severity_score += 20
    
    # Tire pressure check
    if latest.tire_pressure is not None:
        if latest.tire_pressure < 28:
            severity_score += 25
        elif latest.tire_pressure < 30:
            severity_score += 10
    
    return min(severity_score, 100)

def analyze_historical_demand(region, days_back=30):
    """
    Analyze historical maintenance demand for a region
    Returns average daily demand and trend
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get service centers in region
    centers = ServiceCenter.query.filter_by(region=region, is_active=True).all()
    center_ids = [c.center_id for c in centers]
    
    if not center_ids:
        return {'avg_daily_demand': 0, 'trend': 'stable', 'total_capacity': 0}
    
    # Get historical bookings
    bookings = Booking.query.filter(
        Booking.center_id.in_(center_ids),
        Booking.created_at >= cutoff_date
    ).all()
    
    # Calculate daily demand
    daily_counts = defaultdict(int)
    for booking in bookings:
        date_key = booking.created_at.date()
        daily_counts[date_key] += 1
    
    avg_daily_demand = sum(daily_counts.values()) / max(len(daily_counts), 1)
    
    # Calculate trend (simple: compare first half vs second half)
    sorted_dates = sorted(daily_counts.keys())
    if len(sorted_dates) >= 7:
        mid_point = len(sorted_dates) // 2
        first_half_avg = sum(daily_counts[d] for d in sorted_dates[:mid_point]) / mid_point
        second_half_avg = sum(daily_counts[d] for d in sorted_dates[mid_point:]) / (len(sorted_dates) - mid_point)
        
        if second_half_avg > first_half_avg * 1.1:
            trend = 'increasing'
        elif second_half_avg < first_half_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    # Calculate total capacity
    total_capacity = sum(c.capacity_bays for c in centers)
    
    return {
        'avg_daily_demand': round(avg_daily_demand, 2),
        'trend': trend,
        'total_capacity': total_capacity,
        'historical_bookings': len(bookings)
    }

def predict_maintenance_flags(region, forecast_days=7):
    """
    Predict how many vehicles will be flagged for maintenance
    Based on telemetry patterns
    """
    # Get vehicles with recent telemetry
    recent_telemetry = Telemetry.query.filter(
        Telemetry.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    # Group by vehicle
    vehicle_telemetry = defaultdict(list)
    for t in recent_telemetry:
        vehicle_telemetry[t.vehicle_id].append(t)
    
    # Count vehicles likely to need maintenance
    likely_maintenance = 0
    for vehicle_id, telemetry_records in vehicle_telemetry.items():
        severity = calculate_severity_from_telemetry(
            sorted(telemetry_records, key=lambda x: x.timestamp, reverse=True)
        )
        if severity >= 40:  # Medium severity or higher
            likely_maintenance += 1
    
    # Project for forecast period (simple linear projection)
    daily_rate = likely_maintenance / 7  # Current weekly rate
    projected_flags = int(daily_rate * forecast_days)
    
    return projected_flags

def calculate_capacity_utilization(region, window_start, window_end):
    """
    Calculate expected capacity utilization for a region
    """
    centers = ServiceCenter.query.filter_by(region=region, is_active=True).all()
    if not centers:
        return 0.0
    
    center_ids = [c.center_id for c in centers]
    total_capacity = sum(c.capacity_bays for c in centers)
    
    # Get bookings in the window
    bookings = Booking.query.filter(
        Booking.center_id.in_(center_ids),
        Booking.slot_start >= window_start,
        Booking.slot_start < window_end,
        Booking.status.in_(['provisional', 'confirmed', 'in_progress'])
    ).count()
    
    # Calculate slots available in window
    days_in_window = (window_end - window_start).days
    operating_hours = 10  # Average 10 hours per day
    slots_per_day = operating_hours * total_capacity
    total_slots = slots_per_day * days_in_window
    
    if total_slots == 0:
        return 0.0
    
    utilization = (bookings / total_slots) * 100
    return round(min(utilization, 100), 2)

def generate_forecast_for_region(region, forecast_days=7):
    """
    Generate demand forecast for a specific region
    """
    logger.info(f"📊 Generating forecast for region: {region}")
    
    # Analyze historical demand
    historical = analyze_historical_demand(region)
    
    # Predict new maintenance flags
    predicted_flags = predict_maintenance_flags(region, forecast_days)
    
    # Apply trend multiplier
    trend_multiplier = 1.0
    if historical['trend'] == 'increasing':
        trend_multiplier = 1.2
    elif historical['trend'] == 'decreasing':
        trend_multiplier = 0.8
    
    # Calculate estimated requests
    base_demand = historical['avg_daily_demand'] * forecast_days
    estimated_requests = int((base_demand + predicted_flags) * trend_multiplier)
    
    # Calculate capacity utilization
    window_start = datetime.utcnow()
    window_end = window_start + timedelta(days=forecast_days)
    
    capacity_util = calculate_capacity_utilization(region, window_start, window_end)
    
    # Determine confidence level
    if historical['historical_bookings'] >= 20:
        confidence = 0.85
    elif historical['historical_bookings'] >= 10:
        confidence = 0.70
    else:
        confidence = 0.50
    
    # Create forecast record
    forecast = Forecast(
        region=region,
        window_start=window_start,
        window_end=window_end,
        estimated_requests=estimated_requests,
        confidence_level=confidence,
        capacity_utilization=capacity_util
    )
    
    db.session.add(forecast)
    
    return {
        'region': region,
        'window_start': window_start.isoformat(),
        'window_end': window_end.isoformat(),
        'estimated_requests': estimated_requests,
        'confidence_level': confidence,
        'capacity_utilization': capacity_util,
        'historical_data': historical,
        'predicted_flags': predicted_flags
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'forecasting_service',
        'version': '1.0.0'
    })

@app.route('/api/forecast/generate', methods=['POST'])
def generate_forecast():
    """
    Generate forecasts for all regions or specific regions
    Body: {
        "regions": ["North Delhi", "South Delhi"],  # Optional
        "forecast_days": 7  # Optional, default 7
    }
    """
    try:
        data = request.json or {}
        forecast_days = data.get('forecast_days', FORECAST_CONFIG['forecast_days'])
        specified_regions = data.get('regions')
        
        # Get all regions if not specified
        if specified_regions:
            regions = specified_regions
        else:
            all_centers = ServiceCenter.query.filter_by(is_active=True).all()
            regions = list(set(c.region for c in all_centers))
        
        forecasts = []
        for region in regions:
            forecast_data = generate_forecast_for_region(region, forecast_days)
            forecasts.append(forecast_data)
        
        db.session.commit()
        
        logger.info(f"✅ Generated {len(forecasts)} forecasts")
        
        return jsonify({
            'success': True,
            'forecasts': forecasts,
            'generated_at': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error generating forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast/regional', methods=['GET'])
def get_regional_forecasts():
    """
    Get latest forecasts for all regions
    Query params: days (optional, default 7)
    """
    try:
        days = int(request.args.get('days', 7))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get latest forecast for each region
        forecasts = Forecast.query.filter(
            Forecast.generated_at >= cutoff_date
        ).order_by(Forecast.generated_at.desc()).all()
        
        # Group by region and get latest
        region_forecasts = {}
        for forecast in forecasts:
            if forecast.region not in region_forecasts:
                region_forecasts[forecast.region] = forecast
        
        return jsonify({
            'forecasts': [f.to_dict() for f in region_forecasts.values()],
            'count': len(region_forecasts)
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting forecasts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast/capacity', methods=['GET'])
def get_capacity_forecast():
    """
    Get capacity predictions for all service centers
    Query params: region (optional)
    """
    try:
        region = request.args.get('region')
        
        query = ServiceCenter.query.filter_by(is_active=True)
        if region:
            query = query.filter_by(region=region)
        
        centers = query.all()
        
        capacity_data = []
        for center in centers:
            # Calculate utilization for next 7 days
            window_start = datetime.utcnow()
            window_end = window_start + timedelta(days=7)
            
            bookings_count = Booking.query.filter(
                Booking.center_id == center.center_id,
                Booking.slot_start >= window_start,
                Booking.slot_start < window_end,
                Booking.status.in_(['provisional', 'confirmed', 'in_progress'])
            ).count()
            
            # Calculate available capacity
            operating_hours = 10  # Average
            total_slots = operating_hours * center.capacity_bays * 7
            utilization = (bookings_count / total_slots * 100) if total_slots > 0 else 0
            
            capacity_data.append({
                'center_id': center.center_id,
                'name': center.name,
                'region': center.region,
                'capacity_bays': center.capacity_bays,
                'current_bookings': bookings_count,
                'utilization_percent': round(utilization, 2),
                'status': 'high' if utilization > 80 else 'medium' if utilization > 50 else 'low'
            })
        
        return jsonify({
            'capacity_forecast': capacity_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting capacity forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast/feedback', methods=['POST'])
def process_feedback():
    """
    Process feedback from actual bookings to improve forecasts
    Body: {
        "region": "North Delhi",
        "actual_demand": 25,
        "capacity_utilization": 0.85
    }
    """
    try:
        data = request.json
        region = data.get('region')
        actual_demand = data.get('actual_demand')
        capacity_util = data.get('capacity_utilization', 0)
        
        logger.info(f"📥 Received feedback for {region}: demand={actual_demand}, utilization={capacity_util}")
        
        # Adjust multiplier based on capacity utilization
        if capacity_util > FORECAST_CONFIG['capacity_threshold_high']:
            adjustment = FORECAST_CONFIG['multiplier_adjustment']
            logger.info(f"⬆️ High utilization detected. Increasing forecast multiplier.")
        elif capacity_util < FORECAST_CONFIG['capacity_threshold_low']:
            adjustment = -FORECAST_CONFIG['multiplier_adjustment']
            logger.info(f"⬇️ Low utilization detected. Decreasing forecast multiplier.")
        else:
            adjustment = 0
            logger.info(f"✅ Utilization within normal range.")
        
        # In a production system, this would update the multiplier in a config store
        # For prototype, we just log it
        
        return jsonify({
            'success': True,
            'region': region,
            'adjustment': adjustment,
            'message': 'Feedback processed successfully'
        })
    
    except Exception as e:
        logger.error(f"❌ Error processing feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Forecasting Service on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=True)
