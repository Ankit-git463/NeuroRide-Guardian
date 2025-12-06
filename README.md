# Vehicle Maintenance Predictor

## 📌 Project Overview
The **Vehicle Maintenance Predictor** is an AI-powered web application designed to predict whether a vehicle requires maintenance based on various operational parameters. It utilizes a machine learning model (Random Forest) to analyze sensor data and usage metrics, providing actionable insights to fleet managers and vehicle owners.

The system is built using a **Microservices Architecture**, consisting of:
1.  **Gateway Service**: Entry point that orchestrates requests.
2.  **Validation Service**: Handles data validation and risk analysis.
3.  **Prediction Service**: Manages the ML model and inference.
4.  **Frontend**: A modern, responsive dashboard.

## 🚀 Features
- **Predictive Analysis**: Uses a pre-trained Random Forest Classifier to predict maintenance needs with high accuracy.
- **Real-time Validation**: robust input validation system that checks values against defined safety thresholds (e.g., tire pressure, oil quality).
- **Risk Factor Identification**: Automatically identifies and highlights specific risk factors (e.g., "Critical battery status", "Low tire pressure") even if immediate maintenance isn't predicted.
- **Modern UI/UX**: A responsive, professional dashboard interface featuring:
  - Real-time form validation feedback.
  - Dynamic result visualization.
  - Mobile-friendly design using Bootstrap 5.
  - Custom "Glassmorphism" inspired aesthetics.

## 🛠️ Tech Stack

### Backend
- **Python 3.x**: Core programming language.
- **Flask**: Lightweight WSGI web application framework.
- **scikit-learn**: Machine learning library for model inference.
- **Pandas/NumPy**: Data manipulation and processing.
- **Joblib**: Model serialization/deserialization.

### Frontend
- **HTML5**: Semantic markup.
- **CSS3 & Bootstrap 5**: Responsive styling and layout.
- **JavaScript (ES6+)**: Client-side logic and API integration.
- **Google Fonts**: Typography (Inter font family).

## 📂 Project Structure

```
maintenance-predictor/
├── microservices/
│   ├── gateway/               # Orchestrator Service (Port 5000)
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── validation/            # Validation Logic (Port 5001)
│   │   ├── app.py
│   │   ├── thresholds.py
│   │   └── requirements.txt
│   └── prediction/            # ML Inference (Port 5002)
│       ├── app.py
│       ├── model_loader.py
│       ├── maintenance_rf_model.pkl
│       └── requirements.txt
│
├── frontend/
│   ├── index.html             # Main dashboard interface
│   ├── script.js              # Frontend logic
│   └── style.css              # Styling
│
└── README.md                  # Project documentation
```

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8 or higher installed.
- A modern web browser.

### Microservices Setup
You can run all services at once using the provided helper script:

```bash
python run_services.py
```

This will open three separate terminal windows, one for each service (Validation, Prediction, and Gateway).

Alternatively, to run them manually:

**Terminal 1: Validation Service**
```bash
cd microservices/validation
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5001
```

**Terminal 2: Prediction Service**
```bash
cd microservices/prediction
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5002
```

**Terminal 3: Gateway Service**
```bash
cd microservices/gateway
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5000
```

### Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Open `index.html` in your web browser.
    *   You can simply double-click the file, or use a live server extension in VS Code.

## 📖 Usage Guide

1.  **Launch the App**: Ensure the backend server is running and open the frontend in your browser.
2.  **Input Data**: Fill in the vehicle parameters in the form.
    *   **Year of Manufacture**: e.g., 2020
    *   **Usage Hours**: Total hours of operation.
    *   **Load Capacity**: Maximum allowed load.
    *   **Actual Load**: Current load carried.
    *   **Tire Pressure**: Current PSI reading.
    *   **Battery Status**: Percentage charge (0-100).
    *   **Oil Quality**: Rating from 1 (Poor) to 10 (Excellent).
    *   **Brake Condition**: Poor, Fair, or Good.
3.  **Predict**: Click the "Predict Maintenance Need" button.
4.  **View Results**:
    *   **Status**: "Maintenance Required" (Red) or "No Maintenance Needed" (Green).
    *   **Confidence**: The model's certainty percentage.
    *   **Risk Factors**: Specific issues detected (e.g., "Very low tire pressure").
    *   **Recommendation**: Actionable advice based on the prediction.

## 🔍 Validation & Thresholds
The system enforces strict data validation to ensure reliable predictions. These rules are defined in `backend/thresholds.py`.

| Parameter | Min | Max | Risk Thresholds |
|-----------|-----|-----|-----------------|
| Usage Hours | 0 | 50,000 | > 8,000 (High), > 10,000 (Very High) |
| Tire Pressure | 0 | 100 | < 30 (Low), < 28 (Very Low) |
| Oil Quality | 0 | 10 | < 6 (Poor), < 4 (Very Poor) |
| Battery Status | 0 | 100 | < 70% (Low), < 60% (Critical) |

*Note: Inputs outside the Min/Max range will trigger a validation error and prevent prediction.*

## 🔌 API Endpoints

### `GET /`
Returns the API status and version.

### `GET /health`
Health check endpoint to verify if the model is loaded and server is ready.

### `POST /predict`
Main prediction endpoint.
- **Body**: JSON object containing vehicle features.
- **Response**:
  ```json
  {
    "maintenance_required": 1,
    "confidence": 95.5,
    "probability": 0.955,
    "risk_factors": ["Low tire pressure (28 PSI)"]
  }
  ```
- **Error Response (400)**:
  ```json
  {
    "error": "Validation failed: Tire Pressure: Value -5 is below minimum 0",
    "details": ["Tire Pressure: Value -5 is below minimum 0"]
  }
  ```

## 🧠 Model Details
- **Algorithm**: Random Forest Classifier.
- **Input Features**: The model expects 18+ features, including vehicle type, operational metrics, and maintenance history.
- **Handling Missing Data**: The backend (`model_loader.py`) automatically handles missing non-critical features by filling them with default values (0) to ensure the model always receives the expected input shape.
