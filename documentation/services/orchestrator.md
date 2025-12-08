# Orchestrator Service

**Port**: 5005  
**Directory**: `microservices/orchestrator`

## Overview
The **Orchestrator Service** acts as the workflow manager, coordinating multi-step processes that involve multiple microservices. It handles the end-to-end automation cycle from demand forecasting to appointment scheduling and user notification.

## Features
- **Workflow Automation**: executes the "Full Automation Cycle" (Forecast -> Flag -> Schedule -> Notify).
- **Service Coordination**: calls Forecasting, Scheduling, and Telemetry services in sequence.
- **Notification Management**: handles the sending and logging of customer notifications (mocked SMS/Email).

## API Endpoints

### 1. Run Full Cycle
**POST** `/api/orchestrate/full_cycle`

Triggers the complete maintenance workflow.

**Request Body:**
```json
{
  "forecast_days": 7,
  "auto_confirm": true
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "steps": [
      {"step": "forecast_generation", "status": "success"},
      {"step": "scheduling", "status": "success", "scheduled_count": 5}
    ]
  }
}
```

### 2. Schedule Flagged Vehicles
**POST** `/api/orchestrate/schedule_flagged`

Triggers only the scheduling phase for currently flagged vehicles.

### 3. Send Notification
**POST** `/api/notifications/send`

Manually sends a notification for a specific booking.

**Request Body:**
```json
{
  "booking_id": "BKG-123",
  "notification_type": "booking_confirmation"
}
```

### 4. Get Notifications
**GET** `/api/notifications`

Retrieves a log of sent notifications.

## Setup & Run
Run the service:
```bash
python app.py
```
