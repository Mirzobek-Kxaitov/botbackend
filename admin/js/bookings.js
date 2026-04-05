// Bookings Management Script

let bookings = [];
let selectedDate = new Date().toISOString().split('T')[0];

// Load bookings for selected date
async function loadBookings() {
    try {
        const loadingEl = document.getElementById('bookingsTable');
        loadingEl.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Yuklanmoqda...</p>
            </div>
        `;

        bookings = await API.getBookings(selectedDate);
        renderBookings();
        updateStats();
    } catch (error) {
        console.error('Error loading bookings:', error);
        showNotification('Bronlarni yuklashda xatolik', 'error');
    }
}

// Render bookings table
function renderBookings() {
    const tableContainer = document.getElementById('bookingsTable');

    if (bookings.length === 0) {
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📅</div>
                <div class="empty-state-title">Bu sana uchun bronlar yo'q</div>
                <p>Tanlangan sana: ${formatDate(selectedDate)}</p>
            </div>
        `;
        return;
    }

    const tableHtml = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Vaqt</th>
                        <th>Mijoz</th>
                        <th>Telefon</th>
                        <th>Xizmatlar</th>
                        <th>Davomiylik</th>
                        <th>Jami summa</th>
                    </tr>
                </thead>
                <tbody>
                    ${bookings.map(booking => `
                        <tr>
                            <td><strong>#${booking.id}</strong></td>
                            <td>
                                <span class="badge badge-info">${booking.time}</span>
                            </td>
                            <td>${booking.user_name}</td>
                            <td>${booking.user_phone}</td>
                            <td>
                                ${booking.services.map(s => s.service_name).join(', ') || '-'}
                            </td>
                            <td>${booking.total_duration} soat</td>
                            <td><strong>${formatPrice(booking.total_price)}</strong></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = tableHtml;
}

// Update statistics
function updateStats() {
    const totalBookings = bookings.length;
    const totalRevenue = bookings.reduce((sum, b) => sum + b.total_price, 0);

    document.getElementById('totalBookings').textContent = totalBookings;
    document.getElementById('totalRevenue').textContent = formatPrice(totalRevenue);
}

// Change date
function changeDate() {
    selectedDate = document.getElementById('dateSelector').value;
    loadBookings();
}

// Go to today
function goToToday() {
    selectedDate = new Date().toISOString().split('T')[0];
    document.getElementById('dateSelector').value = selectedDate;
    loadBookings();
}

// Go to tomorrow
function goToTomorrow() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    selectedDate = tomorrow.toISOString().split('T')[0];
    document.getElementById('dateSelector').value = selectedDate;
    loadBookings();
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('uz-UZ', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    }).format(date);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('dateSelector').value = selectedDate;
    loadBookings();
});
