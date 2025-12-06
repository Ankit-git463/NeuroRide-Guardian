
# Thresholds and Validation Rules for Maintenance Predictor

THRESHOLDS = {
    'usage_hours': {
        'min': 0,
        'max': 50000,
        'risk_high': 8000,
        'risk_very_high': 10000,
        'label': 'Usage Hours'
    },
    'brake_condition': {
        'allowed_values': [0, 1, 2],
        'risk_poor': 0,
        'risk_fair': 1,
        'label': 'Brake Condition'
    },
    'tire_pressure': {
        'min': 0,
        'max': 100,
        'risk_low': 30,
        'risk_very_low': 28,
        'label': 'Tire Pressure (PSI)'
    },
    'oil_quality': {
        'min': 0,
        'max': 10,
        'risk_poor': 6,
        'risk_very_poor': 4,
        'label': 'Oil Quality'
    },
    'battery_status': {
        'min': 0,
        'max': 100,
        'risk_low': 70,
        'risk_critical': 60,
        'label': 'Battery Status (%)'
    },
    'maintenance_cost': {
        'min': 0,
        'max': 100000,
        'label': 'Maintenance Cost'
    },
    'load_capacity': {
        'min': 0,
        'max': 10000,
        'label': 'Load Capacity'
    },
    'actual_load': {
        'min': 0,
        'max': 100000,
        'label': 'Actual Load'
    },
    'fuel_consumption': {
        'min': 0,
        'max': 1000,
        'label': 'Fuel Consumption'
    },
    'vibration_levels': {
        'min': 0,
        'max': 100,
        'label': 'Vibration Levels'
    }
}

def validate_input(data):
    """
    Validate input data against defined thresholds.
    Returns a list of error messages.
    """
    errors = []
    
    for field, rules in THRESHOLDS.items():
        if field in data:
            value = data[field]
            
            # Type conversion for validation
            try:
                if field == 'brake_condition':
                    value = int(value)
                else:
                    value = float(value)
            except (ValueError, TypeError):
                errors.append(f"{rules['label']}: Invalid format")
                continue

            # Range validation
            if 'min' in rules and value < rules['min']:
                errors.append(f"{rules['label']}: Value {value} is below minimum {rules['min']}")
            
            if 'max' in rules and value > rules['max']:
                errors.append(f"{rules['label']}: Value {value} is above maximum {rules['max']}")
            
            # Allowed values validation
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                errors.append(f"{rules['label']}: Invalid value {value}. Allowed: {rules['allowed_values']}")
                
    return errors

def get_risk_factors(data):
    """
    Analyze data for risk factors based on thresholds.
    Returns a list of risk factor messages.
    """
    risk_factors = []
    
    # Usage Hours
    if 'usage_hours' in data:
        val = float(data['usage_hours'])
        if val > THRESHOLDS['usage_hours']['risk_very_high']:
            risk_factors.append(f"Very high usage hours ({val:,})")
        elif val > THRESHOLDS['usage_hours']['risk_high']:
            risk_factors.append(f"High usage hours ({val:,})")
            
    # Brake Condition
    if 'brake_condition' in data:
        val = int(data['brake_condition'])
        if val == THRESHOLDS['brake_condition']['risk_poor']:
            risk_factors.append("Poor brake condition")
        elif val == THRESHOLDS['brake_condition']['risk_fair']:
            risk_factors.append("Fair brake condition")
            
    # Tire Pressure
    if 'tire_pressure' in data:
        val = float(data['tire_pressure'])
        if val < THRESHOLDS['tire_pressure']['risk_very_low']:
            risk_factors.append(f"Very low tire pressure ({val} PSI)")
        elif val < THRESHOLDS['tire_pressure']['risk_low']:
            risk_factors.append(f"Low tire pressure ({val} PSI)")
            
    # Oil Quality
    if 'oil_quality' in data:
        val = float(data['oil_quality'])
        if val < THRESHOLDS['oil_quality']['risk_very_poor']:
            risk_factors.append(f"Very poor oil quality ({val}/10)")
        elif val < THRESHOLDS['oil_quality']['risk_poor']:
            risk_factors.append(f"Poor oil quality ({val}/10)")
            
    # Battery Status
    if 'battery_status' in data:
        val = float(data['battery_status'])
        if val < THRESHOLDS['battery_status']['risk_critical']:
            risk_factors.append(f"Critical battery status ({val}%)")
        elif val < THRESHOLDS['battery_status']['risk_low']:
            risk_factors.append(f"Low battery status ({val}%)")
            
    return risk_factors
