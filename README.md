# NeuroRide Guardian
**AI-Powered Predictive Maintenance & Scheduling System**

![NeuroRide Guardian Banner](documentation/screenshots/S1-NueroRide%20Guardian.png)

## 1. Executive Summary

**NeuroRide Guardian** is an enterprise-grade vehicle management system designed to shift maintenance paradigms from *reactive* to *predictive*. By ingesting real-time telemetry data from connected vehicles, the system utilizes Machine Learning to predict component failures before they occur. It further leverages Generative AI (Google Gemini) to transform complex technical data into human-readable reports and automatically schedules service appointments based on urgency, customer tier, and service center capacity.

---

## 2. Key Features

- **📡 Real-time Telemetry Ingestion**: Handles live data streams from vehicles (speed, engine load, oil quality, brake wear, tire pressure). Includes a robust **Simulator** for testing and demos.
- **🧠 Predictive Maintenance Engine**: Uses a **Random Forest Machine Learning** model to analyze multivariate risk factors and flag potential failures with high, medium, or low confidence scores.
- **🤖 Generative AI Reporting**: Integrates with **Google Gemini (LLM)** to generate comprehensive, easy-to-understand maintenance reports for vehicle owners, explaining *why* maintenance is needed.
- **📅 Smart Scheduling**: An automated orchestration system that assigns appointment slots using a weighted priority algorithm (considering severity, customer value, and location).
- **📈 Demand Forecasting**: Analyzes historical trends and active maintenance flags to predict future service center utilization and identify capacity bottlenecks.
- **📊 Interactive Dashboards**: A suite of frontend dashboards for Vehicle Owners, Administrators, and Service Staff.

---

## 3. System Architecture

The project is built on a modular **Microservices Architecture**, ensuring scalability and isolation of concerns.

### Microservices Breakdown

| Service | Port | Role | Description |
| :--- | :--- | :--- | :--- |
| **Gateway** | `5000` | API Gateway | The central entry point that routes requests to appropriate backend services. |
| **Core Engine** | `5001` | ML Analysis | Hosts the Scikit-Learn Random Forest model. Validates telemetry and predicts maintenance needs. |
| **LLM Service** | `5002` | Generator | Interfaces with Google Gemini API to create natural language summary reports. |
| **Scheduling** | `5003` | Management | Handles logic for finding slots, assigning technicians, and managing bookings. |
| **Forecasting** | `5004` | Analytics | Predicts weekly service demand based on current fleet health. |
| **Orchestrator** | `5005` | Automation | The "brain" that connects services. It watches for flags and triggers the scheduling workflow. |
| **Telemetry** | `5006` | Ingestion | Receives raw sensor data, serves the simulator, and writes to the telemetry history. |

### Database Schema (SQLite)

The system uses a relational schema managed by **SQLAlchemy**:
- **Vehicles**: Stores static info (VIN, Owner, Model) and dynamic state (Mileage).
- **Telemetry**: Time-series data for sensor readings.
- **MaintenanceFlags**: Risks identified by the ML engine (Severity Score, Risk Factors).
- **ServiceCenters & Technicians**: Capacity planning resources.
- **Bookings**: The end result of the automation—a scheduled appointment.

---

## 4. Technical Stack

*   **Backend**: Python 3.8+, Flask (Microservices), Flask-CORS.
*   **Database**: SQLite, SQLAlchemy ORM.
*   **AI & ML**: 
    *   **Scikit-Learn**: Predictive modeling.
    *   **Google Generative AI**: Text generation.
*   **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js.
*   **Protocols**: HTTP/REST for inter-service communication.

---

## 5. and Setup Guide

### Prerequisites
*   Python 3.8 or higher
*   (Optional) Google Gemini API Key

### Step 1: Installation
Install required dependencies:

```bash
pip install Flask Flask-CORS Flask-SQLAlchemy requests google-generativeai scikit-learn
```

### Step 2: Database Initialization
Populate the database with seed data (vehicles, centers, techs):

```bash
python database/seed_data.py
```

### Step 3: API Key Configuration
Set your Gemini API key for AI reporting features:

*   **Windows (PowerShell):** `$env:GEMINI_API_KEY='your_key'`
*   **Linux/Mac:** `export GEMINI_API_KEY='your_key'`

### Step 4: Running the Backend
Start all microservices using the unified manager:

```bash
python run_services.py
```

### Step 5: Running the Frontend
Serve the static frontend files:

```bash
python -m http.server 8000 --directory frontend
```

---

## 6. User Manual & Workflow

### 1. View the System (Dashboard)
Navigate to `http://localhost:8000/index.html`. This is the user-facing portal to check vehicle status.

### 2. Generate Data (Admin)
Go to `http://localhost:8000/admin.html`:
*   Click **"Start Simulator"** to begin generating fake telemetry for the fleet.
*   Watch data flow in the **Telemetry** page (`/telemetry.html`).

### 3. Automated Analysis
As data comes in, the **Telemetry Service** checks for critical thresholds (e.g., Oil < 3.0).
*   If a risk is found, a **Maintenance Flag** is created.
*   The **Core Engine** validates the risk using the ML model.

### 4. Orchestration
On the **Admin Dashboard**, click **"Run Full Automation Cycle"**.
*   The **Orchestrator** picks up unscheduled flags.
*   It calls **Scheduling Service** to find the best slot based on priority.
*   It calls **LLM Service** to generate a report.
*   Finally, it confirms the booking.

### 5. Review Results
*   **Bookings**: See the newly created appointment in `bookings.html`.
*   **Reports**: View the AI-generated explanation in `report.html` (linked from the booking).

---

## 7. Project Structure

```
maintenance-predictor/
├── database/               # Models (models.py) and Seed Data (seed_data.py)
├── frontend/               # UI Layer
│   ├── admin.html          # Administrator controls
│   ├── bookings.html       # Schedule view
│   ├── index.html          # Main landing
│   ├── telemetry.html      # Live data feed
│   └── js/css              # Assets
├── microservices/          # Application Logic
│   ├── gateway/            # Port 5000
│   ├── core_engine/        # Port 5001
│   ├── llm_service/        # Port 5002
│   ├── scheduling/         # Port 5003
│   ├── forecasting/        # Port 5004
│   ├── orchestrator/       # Port 5005
│   └── telemetry_ingestion/# Port 5006
├── run_services.py         # Service Manager
└── README.md               # This Report
```
