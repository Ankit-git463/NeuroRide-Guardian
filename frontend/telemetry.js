// Telemetry Records JavaScript
const TELEMETRY_API = 'http://localhost:5006';

let allTelemetry = [];
let telemetryChart = null;
let autoRefreshInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTelemetry();
    
    // Event listeners
    document.getElementById('btnFilter').addEventListener('click', applyFilters);
    document.getElementById('btnRefresh').addEventListener('click', loadTelemetry);
    document.getElementById('btnExport').addEventListener('click', exportToCSV);
    document.getElementById('autoRefresh').addEventListener('change', toggleAutoRefresh);
    
    // Start auto-refresh
    toggleAutoRefresh();
});

async function loadTelemetry() {
    try {
        const limit = document.getElementById('filterLimit').value;
        const response = await fetch(`${TELEMETRY_API}/api/telemetry?limit=${limit}`);
        const data = await response.json();
        
        allTelemetry = data.telemetry || [];
        updateStatistics();
        displayTelemetry(allTelemetry);
        updateChart(allTelemetry.slice(0, 20)); // Last 20 for chart
        
    } catch (error) {
        console.error('Error loading telemetry:', error);
        showError('Failed to load telemetry records. Please check if services are running.');
    }
}

function updateStatistics() {
    const total = allTelemetry.length;
    
    // Count by condition
    let critical = 0, warning = 0, good = 0;
    let totalOil = 0;
    const uniqueVehicles = new Set();
    
    allTelemetry.forEach(t => {
        uniqueVehicles.add(t.vehicle_id);
        totalOil += t.oil_quality;
        
        const condition = getCondition(t);
        if (condition === 'critical') critical++;
        else if (condition === 'warning') warning++;
        else good++;
    });
    
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statCritical').textContent = critical;
    document.getElementById('statWarning').textContent = warning;
    document.getElementById('statGood').textContent = good;
    document.getElementById('statVehicles').textContent = uniqueVehicles.size;
    document.getElementById('statAvgOil').textContent = total > 0 ? (totalOil / total).toFixed(1) : '-';
}

function getCondition(telemetry) {
    // Determine condition based on telemetry values
    if (telemetry.oil_quality < 3.0 || 
        telemetry.battery_percent < 50 || 
        telemetry.brake_condition === 'Poor' ||
        telemetry.tire_pressure < 28) {
        return 'critical';
    } else if (telemetry.oil_quality < 5.0 || 
               telemetry.battery_percent < 70 || 
               telemetry.brake_condition === 'Warning' ||
               telemetry.tire_pressure < 30) {
        return 'warning';
    }
    return 'good';
}

function applyFilters() {
    const vehicleFilter = document.getElementById('filterVehicle').value.toLowerCase();
    const conditionFilter = document.getElementById('filterCondition').value;
    
    let filtered = allTelemetry;
    
    // Filter by vehicle
    if (vehicleFilter) {
        filtered = filtered.filter(t => t.vehicle_id.toLowerCase().includes(vehicleFilter));
    }
    
    // Filter by condition
    if (conditionFilter) {
        filtered = filtered.filter(t => getCondition(t) === conditionFilter);
    }
    
    displayTelemetry(filtered);
}

function displayTelemetry(telemetry) {
    const container = document.getElementById('telemetryContainer');
    document.getElementById('recordCount').textContent = telemetry.length;
    
    if (telemetry.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="mt-3 text-muted">No telemetry records found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = telemetry.map(t => createTelemetryCard(t)).join('');
    
    // Add click listeners
    document.querySelectorAll('.telemetry-card').forEach(card => {
        card.addEventListener('click', () => {
            const telemetryId = card.dataset.telemetryId;
            showTelemetryDetails(telemetryId);
        });
    });
}

function createTelemetryCard(telemetry) {
    const condition = getCondition(telemetry);
    const timestamp = new Date(telemetry.timestamp);
    
    return `
        <div class="col-md-6 col-lg-4">
            <div class="card telemetry-card ${condition}" data-telemetry-id="${telemetry.id}" style="cursor: pointer;">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">
                            <i class="bi bi-car-front"></i> ${telemetry.vehicle_id}
                        </h6>
                        <span class="badge bg-${condition === 'critical' ? 'danger' : condition === 'warning' ? 'warning' : 'success'}">
                            ${condition.toUpperCase()}
                        </span>
                    </div>
                    
                    <p class="small text-muted mb-3">
                        <i class="bi bi-clock"></i> ${timestamp.toLocaleString()}
                    </p>
                    
                    <div class="row g-2">
                        <div class="col-6">
                            <span class="metric-badge ${telemetry.oil_quality < 3 ? 'bg-danger' : telemetry.oil_quality < 5 ? 'bg-warning' : 'bg-success'} text-white">
                                <i class="bi bi-droplet"></i> Oil: ${telemetry.oil_quality}
                            </span>
                        </div>
                        <div class="col-6">
                            <span class="metric-badge ${telemetry.battery_percent < 50 ? 'bg-danger' : telemetry.battery_percent < 70 ? 'bg-warning' : 'bg-success'} text-white">
                                <i class="bi bi-battery-half"></i> ${telemetry.battery_percent}%
                            </span>
                        </div>
                        <div class="col-6">
                            <span class="metric-badge ${telemetry.brake_condition === 'Poor' ? 'bg-danger' : telemetry.brake_condition === 'Warning' ? 'bg-warning' : 'bg-success'} text-white">
                                <i class="bi bi-disc"></i> ${telemetry.brake_condition}
                            </span>
                        </div>
                        <div class="col-6">
                            <span class="metric-badge ${telemetry.tire_pressure < 28 ? 'bg-danger' : telemetry.tire_pressure < 30 ? 'bg-warning' : 'bg-success'} text-white">
                                <i class="bi bi-circle"></i> ${telemetry.tire_pressure} PSI
                            </span>
                        </div>
                    </div>
                    
                    <div class="mt-3 small">
                        <i class="bi bi-speedometer"></i> ${telemetry.mileage.toLocaleString()} km
                        <span class="ms-2">
                            <i class="bi bi-fuel-pump"></i> ${telemetry.fuel_consumption} L/100km
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function showTelemetryDetails(telemetryId) {
    const telemetry = allTelemetry.find(t => t.id == telemetryId);
    if (!telemetry) return;
    
    const timestamp = new Date(telemetry.timestamp);
    const condition = getCondition(telemetry);
    
    const detailsHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Basic Information</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Record ID:</th>
                        <td><code>${telemetry.id}</code></td>
                    </tr>
                    <tr>
                        <th>Vehicle ID:</th>
                        <td><strong>${telemetry.vehicle_id}</strong></td>
                    </tr>
                    <tr>
                        <th>Timestamp:</th>
                        <td>${timestamp.toLocaleString()}</td>
                    </tr>
                    <tr>
                        <th>Condition:</th>
                        <td>
                            <span class="badge bg-${condition === 'critical' ? 'danger' : condition === 'warning' ? 'warning' : 'success'}">
                                ${condition.toUpperCase()}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <th>Mileage:</th>
                        <td>${telemetry.mileage.toLocaleString()} km</td>
                    </tr>
                </table>
            </div>
            
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Engine & Performance</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Engine Load:</th>
                        <td>${(telemetry.engine_load * 100).toFixed(0)}%</td>
                    </tr>
                    <tr>
                        <th>Oil Quality:</th>
                        <td>
                            <span class="badge bg-${telemetry.oil_quality < 3 ? 'danger' : telemetry.oil_quality < 5 ? 'warning' : 'success'}">
                                ${telemetry.oil_quality} / 10
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <th>Fuel Consumption:</th>
                        <td>${telemetry.fuel_consumption} L/100km</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <hr>
        
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Electrical System</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Battery:</th>
                        <td>
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar ${telemetry.battery_percent < 50 ? 'bg-danger' : telemetry.battery_percent < 70 ? 'bg-warning' : 'bg-success'}" 
                                     style="width: ${telemetry.battery_percent}%">
                                    ${telemetry.battery_percent}%
                                </div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Braking System</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Brake Condition:</th>
                        <td>
                            <span class="badge bg-${telemetry.brake_condition === 'Poor' ? 'danger' : telemetry.brake_condition === 'Warning' ? 'warning' : 'success'}">
                                ${telemetry.brake_condition}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <th>Brake Temperature:</th>
                        <td>${telemetry.brake_temp}°C</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <hr>
        
        <div class="row">
            <div class="col-12">
                <h6 class="text-muted mb-3">Tire System</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="20%">Tire Pressure:</th>
                        <td>
                            <span class="badge bg-${telemetry.tire_pressure < 28 ? 'danger' : telemetry.tire_pressure < 30 ? 'warning' : 'success'}">
                                ${telemetry.tire_pressure} PSI
                            </span>
                            ${telemetry.tire_pressure < 28 ? '<span class="text-danger ms-2"><i class="bi bi-exclamation-triangle"></i> Critical!</span>' : ''}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    document.getElementById('telemetryDetailsContent').innerHTML = detailsHTML;
    
    const modal = new bootstrap.Modal(document.getElementById('telemetryModal'));
    modal.show();
}

function updateChart(telemetry) {
    const ctx = document.getElementById('telemetryChart').getContext('2d');
    
    // Reverse to show oldest to newest
    const data = telemetry.slice().reverse();
    
    const labels = data.map((t, i) => `#${i + 1}`);
    const oilData = data.map(t => t.oil_quality);
    const batteryData = data.map(t => t.battery_percent);
    const tirePressureData = data.map(t => t.tire_pressure);
    
    if (telemetryChart) {
        telemetryChart.destroy();
    }
    
    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Oil Quality (0-10)',
                    data: oilData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Battery %',
                    data: batteryData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Tire Pressure (PSI)',
                    data: tirePressureData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function toggleAutoRefresh() {
    const autoRefresh = document.getElementById('autoRefresh').checked;
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    if (autoRefresh) {
        autoRefreshInterval = setInterval(loadTelemetry, 5000); // Every 5 seconds
        document.getElementById('liveIndicator').style.display = 'inline-block';
        document.getElementById('liveStatus').textContent = 'Live';
    } else {
        document.getElementById('liveIndicator').style.display = 'none';
        document.getElementById('liveStatus').textContent = 'Paused';
    }
}

function exportToCSV() {
    if (allTelemetry.length === 0) {
        alert('No data to export');
        return;
    }
    
    // Create CSV content
    const headers = ['ID', 'Vehicle ID', 'Timestamp', 'Mileage', 'Engine Load', 'Oil Quality', 
                     'Battery %', 'Brake Condition', 'Brake Temp', 'Tire Pressure', 'Fuel Consumption'];
    
    const rows = allTelemetry.map(t => [
        t.id,
        t.vehicle_id,
        t.timestamp,
        t.mileage,
        t.engine_load,
        t.oil_quality,
        t.battery_percent,
        t.brake_condition,
        t.brake_temp,
        t.tire_pressure,
        t.fuel_consumption
    ]);
    
    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        csvContent += row.join(',') + '\n';
    });
    
    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `telemetry_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

function showError(message) {
    const container = document.getElementById('telemetryContainer');
    container.innerHTML = `
        <div class="col-12">
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${message}
            </div>
        </div>
    `;
}
