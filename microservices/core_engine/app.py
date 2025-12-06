from flask import Flask, request, jsonify
from model_loader import MaintenancePredictor
from thresholds import validate_input, get_risk_factors
import traceback
import os
import logging
import sys

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CoreEngine')

app = Flask(__name__)

# Initialize model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'maintenance_rf_model.pkl')

try:
    predictor = MaintenancePredictor(MODEL_PATH)
    logger.info(f"✅ Model loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Error loading model: {e}")
    traceback.print_exc()
    predictor = None

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Combined endpoint that performs validation and prediction.
    """
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
        
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logger.info("⚙️ Processing analysis request")
            
        # 1. Validation
        validation_errors = validate_input(data)
        if validation_errors:
            logger.warning(f"❌ Validation failed: {validation_errors}")
            return jsonify({
                'status': 'invalid',
                'errors': validation_errors
            }), 200 # Return 200 so gateway handles it gracefully
            
        # 2. Risk Analysis
        risk_factors = get_risk_factors(data)
        
        # 3. Prediction
        result = predictor.predict(data)
        
        # Combine results
        response = {
            'status': 'valid',
            'maintenance_required': result['maintenance_required'],
            'confidence': result['confidence'],
            'probability': result['probability'],
            'risk_factors': risk_factors
        }
        
        logger.info(f"✅ Analysis complete. Maintenance: {result['maintenance_required']}, Confidence: {result['confidence']:.1f}%")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in analyze: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'core_engine',
        'model_loaded': predictor is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
