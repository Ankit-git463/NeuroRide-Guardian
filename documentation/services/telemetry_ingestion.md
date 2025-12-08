# Telemetry Ingestion Service

**Port**: 5006  
**Directory**: `microservices/telemetry_ingestion`

## Overview
The **Telemetry Ingestion Service** is the data entry point for vehicle health metrics. It supports real-time ingestion, bulk CSV import, and includes a built-in simulator to generate realistic test data streams. It also performs the first pass of analysis to "flag" vehicles for maintenance.

## Features
- **Data Ingestion**: accepts JSON payloads of vehicle telemetry.
- **Maintenance Flagging**: automatically checks incoming data against severity thresholds (e.g., Oil < 3.0, Battery < 50%) and flags vehicles.
- **Streaming Simulator**: background thread that generates random, realistic telemetry for registered vehicles.
- **CSV Import**: supports bulk data loading for historical analysis.

## API Endpoints

### 1. Ingest Telemetry
**POST** `/api/ingest_telemetry`

Accepts a single telemetry record.

**Request Body:**
```json
{
  "vehicle_id": "V001",
  "mileage": 50000,
  "oil_quality": 4.5,
  ...
}
```

### 2. Start Simulator
**POST** `/api/simulator/start`

Starts the background simulator thread.

### 3. Stop Simulator
**POST** `/api/simulator/stop`

Stops the background simulator thread.

### 4. Import CSV
**POST** `/api/import_csv`

Upload a CSV file containing telemetry records.

**Form Data:** `file` (CSV file)

### 5. Get Telemetry
**GET** `/api/telemetry`

**Query Params:** `vehicle_id`, `limit`

Retrieves historical telemetry records.

## Setup & Run
Run the service:
```bash
python app.py
```
