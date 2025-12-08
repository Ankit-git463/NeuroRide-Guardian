// Bookings Management JavaScript
const SCHEDULING_API = 'http://localhost:5003';
const ORCHESTRATOR_API = 'http://localhost:5005';

let allBookings = [];
let currentFilter = {
    status: '',
    center: '',
    vehicle: '',
    date: ''
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadBookings();
    
    // Event listeners
    document.getElementById('btnSearch').addEventListener('click', applyFilters);
    document.getElementById('btnRefresh').addEventListener('click', loadBookings);
    document.getElementById('btnConfirmBooking').addEventListener('click', confirmBooking);
    
    // Filter chips
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            currentFilter.status = this.dataset.status;
            applyFilters();
        });
    });
    
    // Search on Enter key
    document.getElementById('searchVehicle').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') applyFilters();
    });
});

async function loadBookings() {
    try {
        const response = await fetch(`${SCHEDULING_API}/api/bookings`);
        const data = await response.json();
        
        allBookings = data.bookings || [];
        updateStatistics();
        displayBookings(allBookings);
        
    } catch (error) {
        console.error('Error loading bookings:', error);
        showError('Failed to load bookings. Please check if services are running.');
    }
}

function updateStatistics() {
    const total = allBookings.length;
    const provisional = allBookings.filter(b => b.status === 'provisional').length;
    const confirmed = allBookings.filter(b => b.status === 'confirmed').length;
    const completed = allBookings.filter(b => b.status === 'completed').length;
    
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statProvisional').textContent = provisional;
    document.getElementById('statConfirmed').textContent = confirmed;
    document.getElementById('statCompleted').textContent = completed;
}

function applyFilters() {
    currentFilter.vehicle = document.getElementById('searchVehicle').value.toLowerCase();
    currentFilter.center = document.getElementById('filterCenter').value;
    currentFilter.date = document.getElementById('filterDate').value;
    
    let filtered = allBookings;
    
    // Filter by status
    if (currentFilter.status) {
        filtered = filtered.filter(b => b.status === currentFilter.status);
    }
    
    // Filter by vehicle
    if (currentFilter.vehicle) {
        filtered = filtered.filter(b => 
            b.vehicle_id.toLowerCase().includes(currentFilter.vehicle)
        );
    }
    
    // Filter by center
    if (currentFilter.center) {
        filtered = filtered.filter(b => b.center_id === currentFilter.center);
    }
    
    // Filter by date
    if (currentFilter.date) {
        filtered = filtered.filter(b => {
            const bookingDate = new Date(b.slot_start).toISOString().split('T')[0];
            return bookingDate === currentFilter.date;
        });
    }
    
    displayBookings(filtered);
}

function displayBookings(bookings) {
    const container = document.getElementById('bookingsContainer');
    document.getElementById('bookingCount').textContent = bookings.length;
    
    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="mt-3 text-muted">No bookings found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = bookings.map(booking => createBookingCard(booking)).join('');
    
    // Add click listeners
    document.querySelectorAll('.booking-card').forEach(card => {
        card.addEventListener('click', () => {
            const bookingId = card.dataset.bookingId;
            showBookingDetails(bookingId);
        });
    });
}

function createBookingCard(booking) {
    const slotDate = new Date(booking.slot_start);
    const statusColors = {
        'provisional': 'warning',
        'confirmed': 'success',
        'in_progress': 'info',
        'completed': 'primary',
        'cancelled': 'danger'
    };
    
    const priorityClass = booking.priority_score >= 70 ? 'priority-high' :
                         booking.priority_score >= 50 ? 'priority-medium' : 'priority-low';
    
    return `
        <div class="col-md-6 col-lg-4">
            <div class="card booking-card h-100" data-booking-id="${booking.booking_id}">
                <div class="priority-indicator ${priorityClass}"></div>
                <div class="card-body ps-4">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">
                            <i class="bi bi-car-front"></i> ${booking.vehicle_id}
                        </h6>
                        <span class="badge status-badge bg-${statusColors[booking.status]}">
                            ${booking.status.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>
                    
                    <p class="mb-2">
                        <i class="bi bi-calendar-event text-primary"></i>
                        <strong>${slotDate.toLocaleDateString()}</strong>
                        at ${slotDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                    
                    <p class="mb-2 small text-muted">
                        <i class="bi bi-building"></i> ${getCenterName(booking.center_id)}
                    </p>
                    
                    ${booking.tech_id ? `
                        <p class="mb-2 small">
                            <i class="bi bi-person-badge"></i> ${booking.tech_id}
                        </p>
                    ` : ''}
                    
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <span class="badge bg-light text-dark">
                            <i class="bi bi-star-fill text-warning"></i> 
                            Priority: ${booking.priority_score.toFixed(1)}
                        </span>
                        <span class="badge bg-${getSeverityColor(booking.severity_level)}">
                            ${booking.severity_level ? booking.severity_level.toUpperCase() : 'N/A'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getCenterName(centerId) {
    const centers = {
        'SC001': 'North Delhi',
        'SC002': 'South Delhi',
        'SC003': 'Gurgaon',
        'SC004': 'Noida',
        'SC005': 'Faridabad'
    };
    return centers[centerId] || centerId;
}

function getSeverityColor(severity) {
    const colors = {
        'critical': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'success'
    };
    return colors[severity] || 'secondary';
}

async function showBookingDetails(bookingId) {
    const booking = allBookings.find(b => b.booking_id === bookingId);
    if (!booking) return;
    
    const slotStart = new Date(booking.slot_start);
    const slotEnd = new Date(booking.slot_end);
    
    const detailsHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Booking Information</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Booking ID:</th>
                        <td><code>${booking.booking_id}</code></td>
                    </tr>
                    <tr>
                        <th>Vehicle ID:</th>
                        <td><strong>${booking.vehicle_id}</strong></td>
                    </tr>
                    <tr>
                        <th>Status:</th>
                        <td>
                            <span class="badge bg-${booking.status === 'confirmed' ? 'success' : 'warning'}">
                                ${booking.status.toUpperCase()}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <th>Priority Score:</th>
                        <td>${booking.priority_score.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <th>Severity:</th>
                        <td>
                            <span class="badge bg-${getSeverityColor(booking.severity_level)}">
                                ${booking.severity_level ? booking.severity_level.toUpperCase() : 'N/A'}
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="col-md-6">
                <h6 class="text-muted mb-3">Appointment Details</h6>
                <table class="table table-sm">
                    <tr>
                        <th width="40%">Service Center:</th>
                        <td>${getCenterName(booking.center_id)}</td>
                    </tr>
                    <tr>
                        <th>Technician:</th>
                        <td>${booking.tech_id || 'Not assigned'}</td>
                    </tr>
                    <tr>
                        <th>Date:</th>
                        <td>${slotStart.toLocaleDateString()}</td>
                    </tr>
                    <tr>
                        <th>Time:</th>
                        <td>${slotStart.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                            ${slotEnd.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                    </tr>
                    <tr>
                        <th>Duration:</th>
                        <td>${booking.estimated_duration_minutes} minutes</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <hr>
        
        <div class="booking-timeline">
            <h6 class="text-muted mb-3">Timeline</h6>
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <small class="text-muted">Created</small>
                <p class="mb-0">${new Date(booking.created_at).toLocaleString()}</p>
            </div>
            ${booking.confirmed_at ? `
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #198754;"></div>
                    <small class="text-muted">Confirmed</small>
                    <p class="mb-0">${new Date(booking.confirmed_at).toLocaleString()}</p>
                </div>
            ` : ''}
            ${booking.completed_at ? `
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #0d6efd;"></div>
                    <small class="text-muted">Completed</small>
                    <p class="mb-0">${new Date(booking.completed_at).toLocaleString()}</p>
                </div>
            ` : ''}
        </div>
        
        ${booking.notes ? `
            <hr>
            <h6 class="text-muted mb-2">Notes</h6>
            <p class="mb-0">${booking.notes}</p>
        ` : ''}
    `;
    
    document.getElementById('bookingDetailsContent').innerHTML = detailsHTML;
    
    // Show confirm button if provisional
    const confirmBtn = document.getElementById('btnConfirmBooking');
    if (booking.status === 'provisional') {
        confirmBtn.style.display = 'block';
        confirmBtn.dataset.bookingId = bookingId;
    } else {
        confirmBtn.style.display = 'none';
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
    modal.show();
}

async function confirmBooking() {
    const bookingId = document.getElementById('btnConfirmBooking').dataset.bookingId;
    const btn = document.getElementById('btnConfirmBooking');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Confirming...';
    
    try {
        const response = await fetch(`${SCHEDULING_API}/api/confirmBooking`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                booking_id: bookingId,
                customer_contact: {
                    name: 'Customer',
                    phone: '9000000000'
                }
            })
        });
        
        if (response.ok) {
            // Send notification
            await fetch(`${ORCHESTRATOR_API}/api/notifications/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    booking_id: bookingId,
                    notification_type: 'booking_confirmation'
                })
            });
            
            // Close modal and reload
            bootstrap.Modal.getInstance(document.getElementById('bookingModal')).hide();
            showSuccess('Booking confirmed and notification sent!');
            await loadBookings();
        } else {
            showError('Failed to confirm booking');
        }
    } catch (error) {
        console.error('Error confirming booking:', error);
        showError('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check-circle"></i> Confirm Booking';
    }
}

function showError(message) {
    const container = document.getElementById('bookingsContainer');
    container.innerHTML = `
        <div class="col-12">
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${message}
            </div>
        </div>
    `;
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        <i class="bi bi-check-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}
