// Simple authentication (for now, just a password check)
// In production, this should be server-side with proper authentication

const ADMIN_PASSWORD = 'admin123'; // TODO: Move to environment variable

class Auth {
    static isAuthenticated() {
        return sessionStorage.getItem('admin_authenticated') === 'true';
    }

    static login(password) {
        if (password === ADMIN_PASSWORD) {
            sessionStorage.setItem('admin_authenticated', 'true');
            return true;
        }
        return false;
    }

    static logout() {
        sessionStorage.removeItem('admin_authenticated');
        window.location.href = 'index.html';
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'index.html';
        }
    }
}

// Check authentication on protected pages
if (window.location.pathname.includes('dashboard') ||
    window.location.pathname.includes('barbers') ||
    window.location.pathname.includes('services') ||
    window.location.pathname.includes('bookings')) {
    Auth.requireAuth();
}
