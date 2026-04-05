// Services Management Script

let services = [];
let barbers = [];
let editingServiceId = null;

// Load services and barbers on page load
async function loadServices() {
    try {
        const loadingEl = document.getElementById('servicesTable');
        loadingEl.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Yuklanmoqda...</p>
            </div>
        `;

        // Load both services and barbers
        [services, barbers] = await Promise.all([
            API.getServices(),
            API.getBarbers()
        ]);

        renderServices();
    } catch (error) {
        console.error('Error loading services:', error);
        showNotification('Xizmatlarni yuklashda xatolik', 'error');
    }
}

// Render services table
function renderServices() {
    const tableContainer = document.getElementById('servicesTable');

    if (services.length === 0) {
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✂️</div>
                <div class="empty-state-title">Hali xizmatlar yo'q</div>
                <p>Yangi xizmat qo'shish uchun yuqoridagi "Yangi xizmat" tugmasini bosing</p>
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
                        <th>Xizmat nomi</th>
                        <th>Sartarosh</th>
                        <th>Narx</th>
                        <th>Davomiylik</th>
                        <th>Kategoriya</th>
                        <th>Holat</th>
                        <th>Harakatlar</th>
                    </tr>
                </thead>
                <tbody>
                    ${services.map(service => {
                        const barber = barbers.find(b => b.id === service.barber_id);
                        return `
                            <tr>
                                <td>${service.id}</td>
                                <td><strong>${service.name}</strong></td>
                                <td>${barber ? barber.name : 'Noma\'lum'}</td>
                                <td>${formatPrice(service.price)}</td>
                                <td>${service.duration} soat</td>
                                <td>
                                    <span class="badge badge-info">
                                        ${service.gender_category === 'male' ? 'Erkak' :
                                          service.gender_category === 'female' ? 'Ayol' : 'Ikkala jins'}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge ${service.is_active ? 'badge-success' : 'badge-danger'}">
                                        ${service.is_active ? 'Faol' : 'Nofaol'}
                                    </span>
                                </td>
                                <td>
                                    <button onclick="editService(${service.id})" class="btn btn-secondary btn-sm">
                                        ✏️ Tahrirlash
                                    </button>
                                    <button onclick="deleteService(${service.id})" class="btn btn-danger btn-sm">
                                        🗑️ O'chirish
                                    </button>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = tableHtml;
}

// Populate barber dropdown
function populateBarberDropdown() {
    const select = document.getElementById('serviceBarber');
    select.innerHTML = barbers.map(barber =>
        `<option value="${barber.id}">${barber.name}</option>`
    ).join('');
}

// Open modal for adding new service
function openAddModal() {
    if (barbers.length === 0) {
        showNotification('Avval sartarosh qo\'shing!', 'warning');
        return;
    }

    editingServiceId = null;
    document.getElementById('modalTitle').textContent = 'Yangi xizmat qo\'shish';
    document.getElementById('serviceForm').reset();
    populateBarberDropdown();
    document.getElementById('serviceModal').classList.add('active');
}

// Open modal for editing service
async function editService(id) {
    try {
        editingServiceId = id;
        const service = services.find(s => s.id === id);

        if (!service) {
            throw new Error('Xizmat topilmadi');
        }

        document.getElementById('modalTitle').textContent = 'Xizmatni tahrirlash';
        populateBarberDropdown();

        document.getElementById('serviceBarber').value = service.barber_id;
        document.getElementById('serviceName').value = service.name;
        document.getElementById('servicePrice').value = service.price;
        document.getElementById('serviceDuration').value = service.duration;
        document.getElementById('serviceGender').value = service.gender_category;
        document.getElementById('serviceIsActive').checked = service.is_active;

        document.getElementById('serviceModal').classList.add('active');
    } catch (error) {
        console.error('Error loading service:', error);
        showNotification('Xizmatni yuklashda xatolik', 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('serviceModal').classList.remove('active');
    editingServiceId = null;
}

// Save service (create or update)
async function saveService(event) {
    event.preventDefault();

    const formData = {
        barber_id: parseInt(document.getElementById('serviceBarber').value),
        name: document.getElementById('serviceName').value,
        price: parseFloat(document.getElementById('servicePrice').value),
        duration: parseInt(document.getElementById('serviceDuration').value),
        gender_category: document.getElementById('serviceGender').value,
        is_active: document.getElementById('serviceIsActive').checked,
    };

    try {
        if (editingServiceId) {
            // Update existing service
            const { barber_id, ...updateData } = formData; // Remove barber_id from update
            await API.updateService(editingServiceId, updateData);
            showNotification('Xizmat muvaffaqiyatli yangilandi!', 'success');
        } else {
            // Create new service
            await API.createService(formData);
            showNotification('Xizmat muvaffaqiyatli qo\'shildi!', 'success');
        }

        closeModal();
        loadServices();
    } catch (error) {
        console.error('Error saving service:', error);
        showNotification(error.message || 'Xatolik yuz berdi', 'error');
    }
}

// Delete service
async function deleteService(id) {
    const service = services.find(s => s.id === id);

    if (!confirm(`"${service.name}" xizmatini o'chirmoqchimisiz?`)) {
        return;
    }

    try {
        await API.deleteService(id);
        showNotification('Xizmat muvaffaqiyatli o\'chirildi!', 'success');
        loadServices();
    } catch (error) {
        console.error('Error deleting service:', error);
        showNotification(error.message || 'O\'chirishda xatolik', 'error');
    }
}

// Filter services
function filterServices() {
    const barberFilter = document.getElementById('filterBarber').value;
    const genderFilter = document.getElementById('filterGender').value;
    const statusFilter = document.getElementById('filterStatus').value;

    let filtered = [...services];

    if (barberFilter) {
        filtered = filtered.filter(s => s.barber_id === parseInt(barberFilter));
    }

    if (genderFilter) {
        filtered = filtered.filter(s => s.gender_category === genderFilter);
    }

    if (statusFilter !== '') {
        filtered = filtered.filter(s => s.is_active === (statusFilter === 'true'));
    }

    // Temporarily replace services array for rendering
    const originalServices = services;
    services = filtered;
    renderServices();
    services = originalServices;
}

// Clear filters
function clearFilters() {
    document.getElementById('filterBarber').value = '';
    document.getElementById('filterGender').value = '';
    document.getElementById('filterStatus').value = '';
    renderServices();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadServices();

    document.getElementById('serviceForm').addEventListener('submit', saveService);
});
