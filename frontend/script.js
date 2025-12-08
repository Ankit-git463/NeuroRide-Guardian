const API_URL = 'http://localhost:5000';  // Backend URL

// Store last prediction data for report generation
let lastPredictionData = null;
let lastPredictionResult = null;

// Load state on page load
window.addEventListener('load', async () => {
    // Health Check (non-blocking)
    setTimeout(async () => {
        try {
            const response = await fetch(`${API_URL}/health`);
            const data = await response.json();
            console.log('Backend health check:', data);
        } catch (error) {
            console.error('Backend connection failed:', error);
        }
    }, 100); // Delay health check to avoid blocking page load

    // Check navigation type to handle "Clear on Refresh"
    // Using performance.getEntriesByType("navigation") for modern browsers
    const navEntries = performance.getEntriesByType("navigation");
    let isReload = false;
    if (navEntries.length > 0 && navEntries[0].type === 'reload') {
        isReload = true;
    } else if (performance.navigation && performance.navigation.type === 1) {
        // Fallback for older browsers (type 1 is TYPE_RELOAD)
        isReload = true;
    }

    if (isReload) {
        console.log('Page reloaded. Clearing state.');
        localStorage.removeItem('lastPredictionData');
        localStorage.removeItem('lastPredictionResult');
        localStorage.removeItem('lastSummary');
        localStorage.removeItem('maintenanceReport');
        localStorage.removeItem('formValues'); // Clear form values too
        
        // Ensure UI is in initial state
        document.getElementById('guidelines').style.display = 'block';
        document.getElementById('resultsContainer').style.display = 'none';
        return;
    }

    // Restore State (Do NOT clear on load, so back button works)
    const savedResult = localStorage.getItem('lastPredictionResult');
    const savedData = localStorage.getItem('lastPredictionData');
    const savedSummary = localStorage.getItem('lastSummary');
    const savedFormValues = localStorage.getItem('formValues');
    
    // Restore form values asynchronously (non-blocking)
    if (savedFormValues) {
        setTimeout(() => {
            try {
                const formValues = JSON.parse(savedFormValues);
                const form = document.getElementById('predictionForm');
                
                for (const [name, value] of Object.entries(formValues)) {
                    const input = form.elements[name];
                    if (input && input.value !== value) { // Only update if different
                        input.value = value;
                    }
                }
            } catch (error) {
                console.error('Error restoring form values:', error);
            }
        }, 0); // Defer to next event loop
    }
    
    if (savedResult && savedData) {
        lastPredictionResult = JSON.parse(savedResult);
        lastPredictionData = JSON.parse(savedData);
        
        // Hide guidelines, show results
        document.getElementById('guidelines').style.display = 'none';
        document.getElementById('resultsContainer').style.display = 'block';
        
        displayResults(lastPredictionResult);
        
        // Restore summary if exists
        if (savedSummary) {
            const summary = JSON.parse(savedSummary);
            displaySummary(summary);
            document.getElementById('btnReport').style.display = 'none';
            document.getElementById('btnFullReport').style.display = 'block';
        } else {
             document.getElementById('btnReport').style.display = 'block';
             document.getElementById('btnFullReport').style.display = 'none';
        }
    } else {
        // Show guidelines initially
        document.getElementById('guidelines').style.display = 'block';
        document.getElementById('resultsContainer').style.display = 'none';
    }
});

document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    btnText.textContent = 'Analyzing...';
    btnLoader.style.display = 'inline-block';
    
    // Hide guidelines
    document.getElementById('guidelines').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';
    document.getElementById('summarySection').style.display = 'none';
    document.getElementById('actionButtons').style.display = 'none';
    
    // Collect form data
    const formData = new FormData(e.target);
    const data = {};
    const formValues = {}; // Store raw form values for restoration
    
    // Convert form data to proper format
    for (let [key, value] of formData.entries()) {
        formValues[key] = value; // Save original value
        data[key] = parseFloat(value) || 0;
    }
    
    // Save form values to localStorage
    localStorage.setItem('formValues', JSON.stringify(formValues));
    
    // Add default values
    data.maintenance_cost = 500;
    data.vibration_levels = 2.5;
    data.impact_on_efficiency = 0.15;
    data.delivery_times = 45;
    
    // Add current date info
    const now = new Date();
    data.maintenance_year = now.getFullYear();
    data.maintenance_month = now.getMonth() + 1;
    data.maintenance_day = now.getDate();
    data.maintenance_weekday = now.getDay();
    
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            if (response.status === 400 && result.details) {
                const error = new Error('Validation failed');
                error.details = result.details;
                error.isValidation = true;
                throw error;
            }
            throw new Error(result.error || 'Prediction failed');
        }
        
        // Store state
        lastPredictionData = data;
        lastPredictionResult = result;
        localStorage.setItem('lastPredictionData', JSON.stringify(data));
        localStorage.setItem('lastPredictionResult', JSON.stringify(result));
        // Clear old summary/report
        localStorage.removeItem('lastSummary');
        localStorage.removeItem('maintenanceReport');
        
        displayResults(result);
        
        // Show buttons
        document.getElementById('actionButtons').style.display = 'grid';
        document.getElementById('btnReport').style.display = 'block';
        document.getElementById('btnFullReport').style.display = 'none';
        
    } catch (error) {
        console.error('Error:', error);
        let errorHtml = '';
        if (error.isValidation) {
            errorHtml = `
                <div class="result-card maintenance-required">
                    <div class="result-title">⚠️ Invalid Input</div>
                    <ul style="text-align: left; margin-top: 10px; color: #d32f2f;">
                        ${error.details.map(detail => `<li>${detail}</li>`).join('')}
                    </ul>
                </div>`;
        } else {
            errorHtml = `
                <div class="result-card maintenance-required">
                    <div class="result-title">❌ Error</div>
                    <p>${error.message}</p>
                </div>`;
        }
        document.getElementById('results').innerHTML = errorHtml;
    } finally {
        btnText.textContent = 'Predict Maintenance Need';
        btnLoader.style.display = 'none';
    }
});

function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    
    // Apply 60% confidence threshold
    const confidence = result.confidence || 0;
    const needsMaintenance = (result.maintenance_required === 1 && confidence > 60);
    
    let html = `
        <div class="result-card ${needsMaintenance ? 'maintenance-required' : 'maintenance-not-required'}">
            <div class="result-title">
                ${needsMaintenance ? 'Maintenance Required' : 'No Maintenance Needed'}
            </div>
    `;
    
    if (result.risk_factors && result.risk_factors.length > 0) {
        // Show "Minor Warnings" if maintenance not required, otherwise "Risk Factors"
        const sectionTitle = needsMaintenance ? 'Risk Factors:' : 'Minor Warnings:';
        
        html += `
            <div class="risk-factors">
                <h3>${sectionTitle}</h3>
                <ul>
                    ${result.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    html += `</div>`;
    resultsDiv.innerHTML = html;
}

function displaySummary(summaryPoints) {
    const summaryList = document.getElementById('summaryList');
    
    // Helper to format text (bolding)
    const formatText = (text) => {
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    };

    if (Array.isArray(summaryPoints)) {
        summaryList.innerHTML = summaryPoints.map(point => `<li>${formatText(point)}</li>`).join('');
    } else {
        summaryList.innerHTML = `<li>${formatText(summaryPoints)}</li>`;
    }
    document.getElementById('summarySection').style.display = 'block';
}

// Handle Report Generation
document.getElementById('btnReport').addEventListener('click', async function() {
    if (!lastPredictionData || !lastPredictionResult) return;
    
    const btnText = document.getElementById('btnReportText');
    const btnLoader = document.getElementById('btnReportLoader');
    
    btnText.textContent = 'Generating...';
    btnLoader.style.display = 'inline-block';
    this.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_data: lastPredictionData,
                prediction_result: lastPredictionResult
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.error || 'Failed to generate report');
        
        if (!data.summary) {
            data.summary = ["Summary not available."];
        }
        
        // Save state
        // Prepend Vehicle Information to the full report
        const vehicleInfo = `
# Vehicle Information
- **Year of Manufacture**: ${lastPredictionData.year_of_manufacture}
- **Vehicle Type**: ${lastPredictionData.vehicle_type === 1 ? 'Van' : 'Truck'}
- **Usage Hours**: ${lastPredictionData.usage_hours} hours
- **Load Status**: ${lastPredictionData.actual_load} / ${lastPredictionData.load_capacity} tons
- **Tire Pressure**: ${lastPredictionData.tire_pressure} PSI
- **Oil Quality**: ${lastPredictionData.oil_quality}/10
- **Battery Status**: ${lastPredictionData.battery_status}%
- **Brake Condition**: ${['Poor', 'Fair', 'Good'][lastPredictionData.brake_condition]}

---
`;
        const finalReport = vehicleInfo + data.full_report;
        
        localStorage.setItem('maintenanceReport', finalReport);
        localStorage.setItem('lastSummary', JSON.stringify(data.summary));
        
        // Update UI
        displaySummary(data.summary);
        document.getElementById('btnReport').style.display = 'none';
        document.getElementById('btnFullReport').style.display = 'block';
        
    } catch (error) {
        console.error(error);
        // Display error in the summary section instead of alert
        const summaryList = document.getElementById('summaryList');
        summaryList.innerHTML = `<li class="text-danger">❌ Error: ${error.message}</li>`;
        document.getElementById('summarySection').style.display = 'block';
    } finally {
        btnText.textContent = '📄 Generate Detailed AI Report';
        btnLoader.style.display = 'none';
        this.disabled = false;
    }
});

// Show Full Report
document.getElementById('btnFullReport').addEventListener('click', function() {
    window.location.href = 'report.html';
});

// Clear Results
document.getElementById('btnClear').addEventListener('click', function() {
    // Clear State
    lastPredictionData = null;
    lastPredictionResult = null;
    localStorage.removeItem('lastPredictionData');
    localStorage.removeItem('lastPredictionResult');
    localStorage.removeItem('lastSummary');
    localStorage.removeItem('maintenanceReport');
    localStorage.removeItem('formValues'); // Clear form values
    
    // Reset form to default values
    document.getElementById('predictionForm').reset();
    
    // Reset UI to Guidelines
    document.getElementById('guidelines').style.display = 'block';
    document.getElementById('resultsContainer').style.display = 'none';
});