# Gateway Service

**Port**: 5000  
**Directory**: `microservices/gateway`

## Overview
The **Gateway Service** acts as the central API entry point for the frontend and external clients. It routes requests to the appropriate microservices (Core Engine, LLM Service, etc.) and handles basic error handling and response formatting.

## Features
- **Centralized Routing**: a single endpoint for clients to interact with the system.
- **Service Integration**: coordinates calls between the Frontend, Core Engine, and LLM Service.
- **Health Aggregation**: provides a unified health status of connected services.

## API Endpoints

### 1. Predict Maintenance
**POST** `/predict`

Forwards the prediction request to the **Core Engine** (`/analyze`).

**Request Body:**
```json
{
  "vehicle_data": { ... }
}
```

### 2. Generate Report
**POST** `/report`

Forwards the report generation request to the **LLM Service** (`/generate_report`).

**Request Body:**
```json
{
  "vehicle_data": { ... },
  "prediction_result": { ... }
}
```

### 3. System Health
**GET** `/health`

Checks the status of the Gateway and its dependent services.

**Response:**
```json
{
  "gateway": "healthy",
  "core_engine": "healthy",
  "llm_service": "healthy"
}
```

### 4. Root Endpoint
**GET** `/`

Returns basic API information.

## Setup & Run
Run the service:
```bash
python app.py
```
