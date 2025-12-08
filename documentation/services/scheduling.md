# Scheduling Service

**Port**: 5003  
**Directory**: `microservices/scheduling`

## Overview
The **Scheduling Service** manages appointment bookings for service centers. It implements a priority-based algorithm to assign slots to vehicles based on urgency, customer status, and other factors.

## Features
- **Priority Scoring**: calculates a score (0-100) based on severity, customer type, proximity, and wait time.
- **Slot Management**: finds available time slots within service center operating hours.
- **Technician Assignment**: matches bookings with available technicians.
- **Batch Processing**: capability to schedule multiple vehicles in a single operation.

## Priority Algorithm
```python
Score = (Severity * 0.4) + (CustomerType * 0.2) + (Proximity * 0.25) - (WaitPenalty * 0.15)
```

## API Endpoints

### 1. Get Available Slots
**GET** `/api/getSlots`

**Query Params:** `center_id`, `date` (YYYY-MM-DD)

Returns a list of available start times for the given day.

### 2. Batch Schedule
**POST** `/api/schedule_batch`

Attempts to schedule appointments for a list of vehicles.

**Request Body:**
```json
{
  "vehicles": ["V001", "V002"],
  "preferred_date_range": {
    "start": "2025-12-08",
    "end": "2025-12-15"
  }
}
```

### 3. Confirm Booking
**POST** `/api/confirmBooking`

Confirms a provisional booking.

**Request Body:**
```json
{
  "booking_id": "BKG-123"
}
```

### 4. List Bookings
**GET** `/api/bookings`

**Query Params:** `status`, `center_id`, `vehicle_id`

Retrieves a list of bookings with optional filters.

## Setup & Run
Run the service:
```bash
python app.py
```
