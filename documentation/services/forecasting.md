# Forecasting Service

**Port**: 5004  
**Directory**: `microservices/forecasting`

## Overview
The **Forecasting Service** predicts future demand for maintenance and analyzes service center capacity. It uses historical booking data and current vehicle telemetry severity to estimate future workloads and optimize resource allocation.

## Features
- **Demand Forecasting**: predicts the number of maintenance requests for the next 7 days.
- **Capacity Utilization**: calculates current and projected utilization of service bays.
- **Trend Analysis**: identifies increasing or decreasing demand trends in specific regions.
- **Feedback Loop**: adjusts forecast models based on actual booking data.

## API Endpoints

### 1. Generate Forecast
**POST** `/api/forecast/generate`

Generates demand forecasts for specified regions or all regions.

**Request Body:**
```json
{
  "regions": ["North Delhi", "South Delhi"], 
  "forecast_days": 7
}
```

**Response:**
```json
{
  "success": true,
  "forecasts": [
    {
      "region": "North Delhi",
      "estimated_requests": 45,
      "confidence_level": 0.85,
      "capacity_utilization": 75.5
    }
  ]
}
```

### 2. Get Regional Forecasts
**GET** `/api/forecast/regional?days=7`

Retrieves the latest generated forecasts for all regions.

### 3. Get Capacity Forecast
**GET** `/api/forecast/capacity?region=North Delhi`

Returns capacity predictions (utilization percentages) for service centers.

**Response:**
```json
{
  "capacity_forecast": [
    {
      "center_id": 1,
      "name": "Delhi Central Hub",
      "utilization_percent": 82.5,
      "status": "high"
    }
  ]
}
```

### 4. Process Feedback
**POST** `/api/forecast/feedback`

Ingests actual demand data to refine future forecasts.

**Request Body:**
```json
{
  "region": "North Delhi",
  "actual_demand": 25,
  "capacity_utilization": 0.85
}
```

## Setup & Run
Run the service:
```bash
python app.py
```
