// Admin Dashboard JavaScript
const API_BASE = 'http://localhost:5000';
const TELEMETRY_API = 'http://localhost:5006';
const SCHEDULING_API = 'http://localhost:5003';
const FORECASTING_API = 'http://localhost:5004';
const ORCHESTRATOR_API = 'http://localhost:5005';

let forecastChart = null;
let capacityChart = null;
let simulatorCheckInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadFlaggedVehicles();
    loadForecasts();
    loadCapacityData();
    checkSimulatorStatus();
    
    // Start periodic updates
    setInterval(loadStatistics, 10000); // Every 10 seconds
    setInterval(checkSimulatorStatus, 5000); // Every 5 seconds
    
    // Event listeners
    document.getElementById('btnStartSimulator').addEventListener('click', startSimulator);
    document.getElementById('btnStopSimulator').addEventListener('click', stopSimulator);
    document.getElementById('btnGenerateForecast').addEventListener('click', generateForecast);
    document.getElementById('btnRefreshFlagged').addEventListener('click', loadFlaggedVehicles);
    document.getElementById('btnScheduleFlagged').addEventListener('click', scheduleFlaggedVehicles);
    document.getElementById('btnFullCycle').addEventListener('click', runFullCycle);
    document.getElementById('btnViewBookings').addEventListener('click', () => {
        window.location.href = 'bookings.html';
    });
});

async function loadStatistics() {
    try {
        // Get simulator status for telemetry count
        const simStatus = await fetch(`${TELEMETRY_API}/api/simulator/status`).then(r => r.json());
        
        document.getElementById('statTelemetry').textContent = simStatus.telemetry_count || 0;
        document.getElementById('statFlagged').textContent = simStatus.flagged_vehicles || 0;
        
        // Get bookings count
        const bookings = await fetch(`${SCHEDULING_API}/api/bookings`).then(r => r.json());
        document.getElementById('statScheduled').textContent = bookings.count || 0;
        
        // Total vehicles (estimate from seed data)
        document.getElementById('statTotalVehicles').textContent = '50';
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadFlaggedVehicles() {
    const tbody = document.getElementById('flaggedVehiclesTable');
    
    try {
        // In a real implementation, we'd have an endpoint to get flagged vehicles
        // For now, we'll use the simulator status
        const simStatus = await fetch(`${TELEMETRY_API}/api/simulator/status`).then(r => r.json());
        
        if (simStatus.flagged_vehicles === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        <i class="bi bi-check-circle fs-3 d-block mb-2"></i>
                        No vehicles currently flagged for maintenance
                    </td>
                </tr>
            `;
            return;
        }
        
        // Mock data for demonstration
        const mockFlagged = [];
        for (let i = 1; i <= Math.min(simStatus.flagged_vehicles, 10); i++) {
            const severityScore = Math.floor(Math.random() * 60) + 40;
            const severity = severityScore >= 80 ? 'critical' : severityScore >= 60 ? 'high' : 'medium';
            
            mockFlagged.push({
                vehicle_id: `V${String(i).padStart(3, '0')}`,
                flagged_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
                severity_score: severityScore,
                severity_level: severity,
                risk_factors: ['Low oil quality', 'Battery warning'],
                is_scheduled: Math.random() > 0.7
            });
        }
        
        tbody.innerHTML = mockFlagged.map(flag => `
            <tr class="flagged-vehicle-row">
                <td><strong>${flag.vehicle_id}</strong></td>
                <td>${new Date(flag.flagged_at).toLocaleDateString()}</td>
                <td>
                    <span class="badge severity-badge bg-${
                        flag.severity_level === 'critical' ? 'danger' :
                        flag.severity_level === 'high' ? 'warning' : 'info'
                    }">
                        ${flag.severity_level.toUpperCase()} (${flag.severity_score})
                    </span>
                </td>
                <td>
                    <small>${flag.risk_factors.join(', ')}</small>
                </td>
                <td>
                    ${flag.is_scheduled ? 
                        '<span class="badge bg-success">Scheduled</span>' :
                        '<span class="badge bg-secondary">Pending</span>'
                    }
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading flagged vehicles:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-danger">
                    Error loading data. Please check if services are running.
                </td>
            </tr>
        `;
    }
}

async function loadForecasts() {
    try {
        const response = await fetch(`${FORECASTING_API}/api/forecast/regional`);
        const data = await response.json();
        
        if (!data.forecasts || data.forecasts.length === 0) {
            // Generate forecasts if none exist
            await generateForecast();
            return;
        }
        
        const regions = data.forecasts.map(f => f.region);
        const estimates = data.forecasts.map(f => f.estimated_requests);
        const utilization = data.forecasts.map(f => f.capacity_utilization);
        
        const ctx = document.getElementById('forecastChart').getContext('2d');
        
        if (forecastChart) {
            forecastChart.destroy();
        }
        
        forecastChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: regions,
                datasets: [
                    {
                        label: 'Estimated Requests',
                        data: estimates,
                        backgroundColor: 'rgba(13, 110, 253, 0.7)',
                        borderColor: 'rgba(13, 110, 253, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Capacity Utilization (%)',
                        data: utilization,
                        backgroundColor: 'rgba(25, 135, 84, 0.7)',
                        borderColor: 'rgba(25, 135, 84, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Requests'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        position: 'right',
                        max: 100,
                        title: {
                            display: true,
                            text: 'Utilization %'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: false
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading forecasts:', error);
    }
}

async function loadCapacityData() {
    try {
        const response = await fetch(`${FORECASTING_API}/api/forecast/capacity`);
        const data = await response.json();
        
        const centers = data.capacity_forecast.map(c => c.name.replace('NeuroRide Service Center - ', ''));
        const utilization = data.capacity_forecast.map(c => c.utilization_percent);
        const colors = data.capacity_forecast.map(c => {
            if (c.status === 'high') return 'rgba(220, 53, 69, 0.7)';
            if (c.status === 'medium') return 'rgba(255, 193, 7, 0.7)';
            return 'rgba(25, 135, 84, 0.7)';
        });
        
        const ctx = document.getElementById('capacityChart').getContext('2d');
        
        if (capacityChart) {
            capacityChart.destroy();
        }
        
        capacityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: centers,
                datasets: [{
                    label: 'Capacity Utilization (%)',
                    data: utilization,
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace('0.7', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Utilization %'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading capacity data:', error);
    }
}

async function checkSimulatorStatus() {
    try {
        const response = await fetch(`${TELEMETRY_API}/api/simulator/status`);
        const data = await response.json();
        
        const indicator = document.getElementById('simulatorIndicator');
        const status = document.getElementById('simulatorStatus');
        const btnStart = document.getElementById('btnStartSimulator');
        const btnStop = document.getElementById('btnStopSimulator');
        
        if (data.running) {
            indicator.className = 'simulator-status running';
            status.textContent = 'Running';
            status.className = 'ms-2 text-success fw-bold';
            btnStart.disabled = true;
            btnStop.disabled = false;
        } else {
            indicator.className = 'simulator-status stopped';
            status.textContent = 'Stopped';
            status.className = 'ms-2 text-muted';
            btnStart.disabled = false;
            btnStop.disabled = true;
        }
        
    } catch (error) {
        console.error('Error checking simulator status:', error);
    }
}

async function startSimulator() {
    try {
        const response = await fetch(`${TELEMETRY_API}/api/simulator/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showActionResult('Telemetry simulator started successfully!', 'success');
            checkSimulatorStatus();
        } else {
            showActionResult('Failed to start simulator', 'danger');
        }
    } catch (error) {
        console.error('Error starting simulator:', error);
        showActionResult('Error: ' + error.message, 'danger');
    }
}

async function stopSimulator() {
    try {
        const response = await fetch(`${TELEMETRY_API}/api/simulator/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showActionResult('Telemetry simulator stopped', 'info');
            checkSimulatorStatus();
        } else {
            showActionResult('Failed to stop simulator', 'danger');
        }
    } catch (error) {
        console.error('Error stopping simulator:', error);
        showActionResult('Error: ' + error.message, 'danger');
    }
}

async function generateForecast() {
    const btn = document.getElementById('btnGenerateForecast');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
    
    try {
        const response = await fetch(`${FORECASTING_API}/api/forecast/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ forecast_days: 7 })
        });
        
        if (response.ok) {
            showActionResult('Forecasts generated successfully!', 'success');
            await loadForecasts();
            await loadCapacityData();
        } else {
            showActionResult('Failed to generate forecasts', 'danger');
        }
    } catch (error) {
        console.error('Error generating forecast:', error);
        showActionResult('Error: ' + error.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Generate';
    }
}

async function scheduleFlaggedVehicles() {
    const btn = document.getElementById('btnScheduleFlagged');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Scheduling...';
    
    try {
        const response = await fetch(`${ORCHESTRATOR_API}/api/orchestrate/schedule_flagged`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showActionResult(
                `Scheduled ${data.scheduled_count} vehicles. Failed: ${data.failed_count}`,
                'success'
            );
            await loadFlaggedVehicles();
            await loadStatistics();
        } else {
            showActionResult('Failed to schedule vehicles', 'danger');
        }
    } catch (error) {
        console.error('Error scheduling vehicles:', error);
        showActionResult('Error: ' + error.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-calendar-plus"></i> Schedule Flagged Vehicles';
    }
}

async function runFullCycle() {
    const btn = document.getElementById('btnFullCycle');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Running...';
    
    try {
        const response = await fetch(`${ORCHESTRATOR_API}/api/orchestrate/full_cycle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                forecast_days: 7,
                auto_confirm: true
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const steps = data.results.steps;
            const successSteps = steps.filter(s => s.status === 'success').length;
            
            showActionResult(
                `Full cycle complete! ${successSteps}/${steps.length} steps successful`,
                'success'
            );
            
            // Refresh all data
            await Promise.all([
                loadStatistics(),
                loadFlaggedVehicles(),
                loadForecasts(),
                loadCapacityData()
            ]);
        } else {
            showActionResult('Full cycle failed', 'danger');
        }
    } catch (error) {
        console.error('Error running full cycle:', error);
        showActionResult('Error: ' + error.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Run Full Automation Cycle';
    }
}

function showActionResult(message, type = 'info') {
    const resultDiv = document.getElementById('actionResult');
    const resultText = document.getElementById('actionResultText');
    
    resultDiv.className = `alert alert-${type} mb-0`;
    resultText.textContent = message;
    resultDiv.classList.remove('d-none');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        resultDiv.classList.add('d-none');
    }, 5000);
}
