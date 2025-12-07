# NeuroRide Guardian
**AI-Powered Vehicle Maintenance & Safety System**

## 📌 Project Overview
**NeuroRide Guardian** is an advanced predictive maintenance system designed to enhance vehicle safety and reliability. By leveraging machine learning (Random Forest) and Generative AI (Gemini), it analyzes vehicle telemetry to predict maintenance needs, identify risk factors, and generate detailed, human-readable technical reports.

The system is built on a robust **Microservices Architecture**, ensuring scalability and modularity.

## 🚀 Key Features
- **🔮 Predictive Maintenance**: Accurately predicts if maintenance is required based on usage, load, and sensor data.
- **⚡ AI-Powered Reports**: Generates detailed, professional maintenance reports with actionable recommendations using Google Gemini AI.
- **🛡️ Risk Analysis**: Automatically flags critical issues (e.g., "Brake Condition Poor", "Low Oil Quality") even if the overall prediction is safe.
- **📊 Interactive Dashboard**: A modern, responsive web interface with real-time feedback and dynamic visualizations.
- **📄 PDF Export**: Ability to generate and print comprehensive maintenance reports for record-keeping.
- **💾 State Persistence**: Automatically saves analysis results, allowing users to navigate away and return without losing data.

## 🛠️ Tech Stack

### Backend (Microservices)
- **Gateway Service (Flask)**: Orchestrates requests between frontend and backend services.
- **Core Engine (Flask + Scikit-Learn)**: Handles data validation and runs the Random Forest prediction model.
- **LLM Service (Flask + Google Gemini)**: Generates natural language summaries and detailed technical reports.

### Frontend
- **HTML5 / CSS3 / JavaScript**: Core web technologies.
- **Bootstrap 5**: Responsive layout and components.
- **Marked.js**: Markdown rendering for AI reports.

## 📂 Project Structure

```
maintenance-predictor/
├── microservices/
│   ├── gateway/               # Entry Point (Port 5000)
│   ├── core_engine/           # Validation & Prediction (Port 5001)
│   └── llm_service/           # AI Report Generation (Port 5002)
│
├── frontend/
│   ├── index.html             # Dashboard
│   ├── report.html            # Detailed Report View
│   ├── script.js              # Logic & API Integration
│   └── style.css              # Custom Styling
│
└── run_services.py            # Helper script to launch all services
```

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- Google Gemini API Key (for AI reports)

### Quick Start
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Ankit-git463/NeuroRide-Guardian.git
    cd NeuroRide-Guardian
    ```

2.  **Set API Key**:
    Set your Gemini API key as an environment variable:
    ```bash
    # Windows (PowerShell)
    $env:GEMINI_API_KEY="your_api_key_here"
    ```

3.  **Run Services**:
    Use the helper script to start all microservices simultaneously:
    ```bash
    python run_services.py
    ```
    *This will launch the Gateway (5000), Core Engine (5001), and LLM Service (5002).*

4.  **Launch Frontend**:
    Open `frontend/index.html` in your browser (or serve it using a simple HTTP server).

## 📖 Usage Guide

1.  **Dashboard**: Enter vehicle details (Year, Usage, Load, Tire Pressure, etc.).
2.  **Predict**: Click "Predict Maintenance Need".
3.  **Analyze**: View the immediate status (Maintenance Required/Not) and specific risk factors.
4.  **Generate Report**: Click "Generate Detailed AI Report" to get a comprehensive analysis.
5.  **Full View**: Click "Show Full Report" to see the detailed breakdown, including technical comparisons and prioritized actions.
6.  **Print**: Use the print button on the report page to save as PDF.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Validates input and returns maintenance prediction + risk factors. |
| `POST` | `/report` | Generates a detailed AI maintenance report based on vehicle data. |
| `GET`  | `/health` | Checks the health status of the backend services. |

## 🧠 Model Details
- **Algorithm**: Random Forest Classifier.
- **Training**: Trained on synthetic vehicle telemetry data covering various failure modes.
- **Validation**: Strict physics-based thresholds ensure inputs are realistic before prediction.
