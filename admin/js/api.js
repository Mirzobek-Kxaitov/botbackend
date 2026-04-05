// API Configuration
const API_BASE_URL = window.location.origin;

// API Helper functions
class API {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Barber endpoints
    static async getBarbers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/barbers${queryString ? '?' + queryString : ''}`);
    }

    static async getBarber(id) {
        return this.request(`/api/barbers/${id}`);
    }

    static async createBarber(data) {
        return this.request('/api/barbers', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    static async updateBarber(id, data) {
        return this.request(`/api/barbers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    static async deleteBarber(id) {
        return this.request(`/api/barbers/${id}`, {
            method: 'DELETE',
        });
    }

    // Service endpoints
    static async getServices(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/services${queryString ? '?' + queryString : ''}`);
    }

    static async getService(id) {
        return this.request(`/api/services/${id}`);
    }

    static async createService(data) {
        return this.request('/api/services', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    static async updateService(id, data) {
        return this.request(`/api/services/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    static async deleteService(id) {
        return this.request(`/api/services/${id}`, {
            method: 'DELETE',
        });
    }

    // Booking endpoints
    static async getBookings(date) {
        return this.request(`/bookings/${date}`);
    }

    static async createBooking(data) {
        return this.request('/bookings', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Available times
    static async getAvailableTimes(date, duration = 1) {
        return this.request(`/available-times/${date}?duration=${duration}`);
    }
}

// Utility functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function formatPrice(price) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'decimal',
        minimumFractionDigits: 0,
    }).format(price) + " so'm";
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('uz-UZ', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
}
