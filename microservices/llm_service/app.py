# app.py
import os
import sys
import json
import traceback
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import google.generativeai as genai

# -------------------------
# Logging configuration
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('LLMService')

# -------------------------
# Flask app
# -------------------------
app = Flask(__name__)

# -------------------------
# Gemini / Generative API configuration
# -------------------------
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')  # set this in your environment

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("✅ Gemini API configured successfully")
    except Exception as e:
        logger.exception("Failed to configure Gemini client: %s", e)
        model = None
else:
    logger.warning("GEMINI_API_KEY not found in environment variables. LLM disabled.")

# -------------------------
# Prompt template and helper
# -------------------------
PROMPT_TEMPLATE = """
SYSTEM: You are a Senior Vehicle Maintenance Engineer responsible for producing an authoritative technical assessment report.
You will receive vehicle telemetry data and diagnostic outputs. Your duty is to produce a final professional maintenance report in strict JSON format.

STRICT LANGUAGE RULES (MANDATORY):
- Do NOT use any wording that implies AI, models, predictions, systems, algorithms, or automated analysis.
  Forbidden phrases include:
    "AI predicts", "AI suggests", "AI indicates",
    "The model shows", "The system predicts",
    "Based on AI analysis", "According to the prediction",
    "Machine learning", "LLM", "Algorithmic assessment".
- Write with the direct, confident tone of a senior automotive engineer.
  Use definitive statements such as:
    "Maintenance is required."
    "The brake system shows critical wear."
    "Immediate action is necessary."
- Never refer to uncertainty caused by AI or modelling.

INDUSTRY STANDARDS (MUST FOLLOW EXACTLY):
- Tire Pressure: 30–35 PSI optimal
- Oil Quality (scale 0–10): > 5.0 Acceptable; < 3.0 Critical
- Battery Health: > 75% Good; < 50% Replace
- Brake Condition: Must be "Good" only. Any other value = Warning or Critical
- Load: actual_load must NOT exceed load_capacity

INPUT DATA:
{input_block}

OUTPUT FORMAT:
Produce ONLY a single JSON object following this schema:

{
  "summary": ["Point 1", "Point 2", ...],
  "components": {
    "tire_pressure": {
      "status": "Good"|"Warning"|"Critical",
      "current": number|"unknown",
      "deviation": number|"N/A",
      "notes": "Short engineering note."
    },
    "oil_quality": {
      "status": "Good"|"Warning"|"Critical",
      "current": number|"unknown",
      "deviation": number|"N/A",
      "notes": "Short engineering note."
    },
    "battery_health": {
      "status": "Good"|"Warning"|"Critical",
      "current": number|"unknown",
      "deviation": number|"N/A",
      "notes": "Short engineering note."
    },
    "brake_condition": {
      "status": "Good"|"Warning"|"Critical",
      "current": "string"|"unknown",
      "deviation": "N/A",
      "notes": "Short engineering note."
    },
    "load_status": {
      "status": "Good"|"Warning"|"Critical",
      "actual_load": number|"unknown",
      "load_capacity": number|"unknown",
      "deviation": number|"N/A",
      "notes": "Short engineering note."
    }
  },
  "model_prediction": {
    "maintenance_required": true|false|"unknown",
    "risk_factors": ["factor1", "factor2"]
  },
  "overall_urgency": "Low"|"Medium"|"High",
  "critical_actions": ["Action 1", "Action 2"],
  "full_report": "Markdown string containing the following sections:
## Summary

## Critical Actions Needed

## Component Analysis

## Recommendations
"
}

ADDITIONAL RULES (STRICT):
1. Use numeric types where applicable; otherwise assign "unknown".
2. Deviation = current_value − nearest_standard_threshold (if relevant), else "N/A".
3. Urgency logic:
   - If any component is **Critical**, or maintenance_required == true → High
   - Else if any component is Warning → Medium
   - Else → Low
4. Each note, summary point, recommendation must be ≤ 20 words.
5. Use **bold Markdown** for:
   - Any Critical status or value
   - Status labels such as **Good**, **Warning**, **Critical**
6. The `full_report` MUST contain proper newlines and follow the exact markdown structure:
   ## Summary
   ## Critical Actions Needed
   ## Component Analysis
   ## Recommendations
7. Tone must be authoritative, engineering-focused, and factual.
8. Do NOT output anything outside the final JSON object.

"""


def safe_num(x):
    """Return a number or 'unknown' (do not throw)."""
    try:
        if x is None:
            return "unknown"
        # if it's a string that looks like a number
        if isinstance(x, str):
            if x.strip() == "":
                return "unknown"
            return float(x) if ('.' in x or 'e' in x.lower()) else int(x)
        return x
    except Exception:
        return "unknown"

def build_input_block(vehicle_data: dict, prediction_result: dict) -> str:
    # Prepare readable input for the model
    # Use "unknown" for missing fields
    v = vehicle_data or {}
    p = prediction_result or {}
    # map brake_condition numeric to label if necessary
    brake_map = {0: "Poor", 1: "Fair", 2: "Good"}
    brake_val = v.get('brake_condition', None)
    try:
        if isinstance(brake_val, (int, float)):
            brake_label = brake_map.get(int(brake_val), str(brake_val))
        else:
            brake_label = str(brake_val) if brake_val is not None else "unknown"
    except Exception:
        brake_label = "unknown"

    input_lines = [
        f"Year: {v.get('year_of_manufacture', 'unknown')}",
        f"Type: {'Van' if v.get('vehicle_type') == 1 else ('Truck' if v.get('vehicle_type') == 2 else v.get('vehicle_type','unknown'))}",
        f"Usage Hours: {v.get('usage_hours', 'unknown')}",
        f"Load: {v.get('actual_load', 'unknown')} tons (Capacity: {v.get('load_capacity','unknown')} tons)",
        f"Tire Pressure: {v.get('tire_pressure', 'unknown')} PSI",
        f"Oil Quality: {v.get('oil_quality', 'unknown')}/10",
        f"Battery Status: {v.get('battery_status', 'unknown')}%",
        f"Brake Condition: {brake_label}",
        "",
        "AI Prediction:",
        f"  maintenance_required: {'YES' if p.get('maintenance_required') else 'NO' if p.get('maintenance_required') is not None else 'unknown'}",
        f"  confidence: {p.get('confidence', 'unknown')}%",
        f"  risk_factors: {', '.join(p.get('risk_factors', [])) if isinstance(p.get('risk_factors'), (list,tuple)) else p.get('risk_factors','[]')}"
    ]
    return "\n".join(input_lines)

# -------------------------
# Utility: parse model response
# -------------------------
def extract_json_from_text(text: str):
    """
    Try to extract and parse a JSON object from text.
    Returns a Python object on success, or raises json.JSONDecodeError on failure.
    """
    text = text.strip()
    # Remove common markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Fast attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first {...} block
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            return json.loads(candidate)  # may raise
        else:
            # Last attempt: try to replace trailing commas and other minor issues
            cleaned = text.replace(",\n}", "\n}").replace(",\r\n}", "\n}").replace(",\n]", "\n]")
            return json.loads(cleaned)

# -------------------------
# Routes
# -------------------------
@app.route('/generate_report', methods=['POST'])
def generate_report():
    if model is None:
        logger.error("LLM not configured; request rejected")
        return jsonify({'error': 'LLM service not configured (Missing API Key)'}), 503

    try:
        payload = request.get_json(force=True)
        vehicle_data = payload.get('vehicle_data', {})
        prediction_result = payload.get('prediction_result', {})

        logger.info("Received generate_report request: vehicle id / type: %s / %s",
                    vehicle_data.get('vehicle_id', 'unknown'), vehicle_data.get('vehicle_type', 'unknown'))

        input_block = build_input_block(vehicle_data, prediction_result)
        prompt = PROMPT_TEMPLATE.replace('{input_block}', input_block)

        # Call the model
        # NOTE: SDK semantics may vary; this follows your prior usage.
        logger.info("Sending prompt to LLM (length=%d chars)", len(prompt))
        response = model.generate_content(prompt)

        # The SDK returns an object — try to pull text safely
        text = None
        if hasattr(response, "text"):
            text = response.text
        else:
            # if response is dict-like or has content
            try:
                text = json.dumps(response)
            except Exception:
                text = str(response)

        if not text:
            raise RuntimeError("Empty response from LLM")

        text = text.strip()
        print(f"\n====== LLM RAW OUTPUT ======\n{text}\n============================\n")
        logger.debug("Raw LLM response: %s", text[:1000])  # log first 1000 chars

        # Attempt to parse JSON produced by the model
        parsed = None
        try:
            parsed = extract_json_from_text(text)
        except Exception as e:
            logger.exception("Failed to parse JSON from LLM response: %s", e)

        final_obj = None
        if isinstance(parsed, dict):
            final_obj = parsed
        else:
            # Fallback: return raw text in full_report and provide a minimal summary
            logger.warning("Parsed response not a dict; falling back to raw text packaging.")
            final_obj = {
                "summary": ["AI response could not be parsed into expected JSON schema."],
                "components": {},
                "model_prediction": {
                    "maintenance_required": prediction_result.get('maintenance_required', "unknown"),
                    "confidence_percent": prediction_result.get('confidence', "unknown"),
                    "risk_factors": prediction_result.get('risk_factors', [])
                },
                "overall_urgency": "Unknown",
                "recommended_next_steps": [],
                "full_report": text
            }

        # Ensure minimal schema keys exist
        if 'summary' not in final_obj or not isinstance(final_obj['summary'], list):
            final_obj.setdefault('summary', ["Summary generated but format was unconventional."])

        if 'full_report' not in final_obj:
            final_obj['full_report'] = text

        # Add/merge vehicle details into response under vehicle_details
        # Keep only safe, serializable fields from vehicle_data
        try:
            vehicle_details_safe = json.loads(json.dumps(vehicle_data))
        except Exception:
            vehicle_details_safe = {k: str(v) for k, v in (vehicle_data or {}).items()}

        final_obj['vehicle_details'] = vehicle_details_safe
        final_obj['generated_at'] = datetime.utcnow().isoformat() + "Z"

        # Return final JSON
        return jsonify(final_obj), 200

    except Exception as e:
        logger.exception("Unhandled error during report generation: %s", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'llm_service',
        'configured': model is not None
    })

if __name__ == '__main__':
    # Run with: export GEMINI_API_KEY="..." && python app.py
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))
