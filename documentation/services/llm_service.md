# LLM Service

**Port**: 5002  
**Directory**: `microservices/llm_service`

## Overview
The **LLM Service** leverages Generative AI (Google Gemini) to produce professional, human-readable technical assessment reports. It translates raw telemetry data and ML predictions into actionable engineering insights.

## Features
- **Generative AI Integration**: uses Google's Gemini Flash model.
- **Professional Persona**: adopts the persona of a Senior Vehicle Maintenance Engineer.
- **Structured Output**: enforces a strict JSON schema for frontend consumption while providing a markdown-formatted full report.
- **Strict Guidelines**: follows rules to avoid "AI" terminology and ensures authoritative language.

## API Endpoints

### 1. Generate Report
**POST** `/generate_report`

Generates the assessment report.

**Request Body:**
```json
{
  "vehicle_data": {
    "vehicle_id": "V123",
    "oil_quality": 2.5,
    ...
  },
  "prediction_result": {
    "maintenance_required": true,
    "confidence": 0.85,
    "risk_factors": ["Low oil"]
  }
}
```

**Response:**
```json
{
  "summary": ["Oil quality is critical.", "Brake pads need inspection."],
  "components": { ... },
  "overall_urgency": "High",
  "full_report": "## Summary\n\nMetric analysis indicates...",
  "vehicle_details": { ... }
}
```

### 2. Health Check
**GET** `/health`

Checks if the service is running and if the Gemini API key is configured.

## Configuration
- **Environment Variable**: `GEMINI_API_KEY` is required for the service to function.

## Setup & Run
1. Set the API key:
   ```powershell
   $env:GEMINI_API_KEY='your_key'
   ```
2. Run the service:
   ```bash
   python app.py
   ```
