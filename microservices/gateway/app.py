from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import traceback
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
logger = logging.getLogger('Gateway')

app = Flask(__name__)
CORS(app)

# Service URLs
CORE_ENGINE_URL = 'http://localhost:5001'
LLM_SERVICE_URL = 'http://localhost:5002'

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Vehicle Maintenance Gateway API',
        'version': '3.0 (Core + LLM)'
    })

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logger.info(f"📥 Received prediction request from {request.remote_addr}")
        
        # Call Core Engine (Validation + Prediction)
        try:
            logger.info(f"➡️ Forwarding to Core Engine: {CORE_ENGINE_URL}")
            core_response = requests.post(f"{CORE_ENGINE_URL}/analyze", json=data)
            if core_response.status_code != 200:
                return jsonify({'error': 'Core engine error'}), 500
                
            result = core_response.json()
            
            if result.get('status') == 'invalid':
                logger.warning(f"❌ Validation failed: {result.get('errors')}")
                return jsonify({
                    'error': f"Validation failed: {'; '.join(result.get('errors'))}",
                    'details': result.get('errors')
                }), 400
                
            logger.info(f"✅ Analysis success. Maintenance: {result.get('maintenance_required')}")
            return jsonify(result)
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ Core engine unavailable")
            return jsonify({'error': 'Core engine unavailable'}), 503

    except Exception as e:
        logger.error(f"❌ Error in predict: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/report', methods=['POST', 'OPTIONS'])
def report():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logger.info("📝 Received report generation request")
        
        # Call LLM Service
        try:
            logger.info(f"➡️ Forwarding to LLM Service: {LLM_SERVICE_URL}")
            llm_response = requests.post(f"{LLM_SERVICE_URL}/generate_report", json=data)
            if llm_response.status_code != 200:
                logger.error(f"❌ LLM Service returned error: {llm_response.status_code}")
                return jsonify(llm_response.json()), llm_response.status_code
                
            logger.info("✅ Report generated successfully")
            return jsonify(llm_response.json())
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ LLM service unavailable")
            return jsonify({'error': 'LLM service unavailable'}), 503

    except Exception as e:
        logger.error(f"❌ Error in report: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    services = {
        'gateway': 'healthy',
        'core_engine': 'unknown',
        'llm_service': 'unknown'
    }
    
    try:
        requests.get(f"{CORE_ENGINE_URL}/health", timeout=1)
        services['core_engine'] = 'healthy'
    except:
        services['core_engine'] = 'down'
        
    try:
        requests.get(f"{LLM_SERVICE_URL}/health", timeout=1)
        services['llm_service'] = 'healthy'
    except:
        services['llm_service'] = 'down'
        
    return jsonify(services)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
