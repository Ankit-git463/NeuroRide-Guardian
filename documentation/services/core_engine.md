# Core Engine Service

**Port**: 5001  
**Directory**: `microservices/core_engine`

## Overview
The **Core Engine** is the primary analytical component responsible for validating input data and predicting maintenance needs. It utilizes a trained Machine Learning model (Random Forest) to analyze vehicle telemetry and determine if maintenance is required.

## Features
- **Input Validation**: checks for required fields and valid data ranges.
- **Risk Analysis**: identifies specific risk factors (e.g., low oil quality, brake issues).
- **ML Prediction**: uses a serialized `.pkl` model to predict maintenance probability.

## API Endpoints

### 1. Analyze Prediction
**POST** `/analyze`

Performs validation, risk analysis, and runs the ML prediction model.

**Request Body:**
```json
{
  "vehicle_id": "V001",
  "oil_quality": 2.5,
  "tire_pressure": 28,
  "brake_condition": "Poor",
  "battery_status": 45,
  ...
}
```

**Response:**
```json
{
  "status": "valid",
  "maintenance_required": true,
  "confidence": 0.85,
  "probability": 0.85,
  "risk_factors": ["Critical oil quality", "Poor brake condition"]
}
```

### 2. Health Check
**GET** `/health`

Returns the health status of the service and whether the ML model is loaded.

**Response:**
```json
{
  "status": "healthy",
  "service": "core_engine",
  "model_loaded": true
}
```

## Setup & Run
1. Ensure the `maintenance_rf_model.pkl` is present in the directory.
2. Run the service:
   ```bash
   python app.py
   ```
