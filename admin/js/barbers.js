// Barbers Management Script

let barbers = [];
let botStatuses = {};
let editingBarberId = null;

// Load barbers on page load
async function loadBarbers() {
    try {
        const loadingEl = document.getElementById('barbersTable');
        loadingEl.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Yuklanmoqda...</p>
            </div>
        `;

        // Load barbers and bot statuses in parallel
        const [barbersData, statusData] = await Promise.all([
            API.getBarbers(),
            API.request('/api/bots/status').catch(() => ({ running_bots: [], manager_active: false }))
        ]);
        barbers = barbersData;

        // Map bot statuses by barber_id
        botStatuses = {};
        if (statusData.running_bots) {
            statusData.running_bots.forEach(b => {
                botStatuses[b.barber_id] = b.is_running;
            });
        }

        renderBarbers();
    } catch (error) {
        console.error('Error loading barbers:', error);
        showNotification('Sartaroshlarni yuklashda xatolik', 'error');
    }
}

// Render barbers table
function renderBarbers() {
    const tableContainer = document.getElementById('barbersTable');

    if (barbers.length === 0) {
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👨‍💼</div>
                <div class="empty-state-title">Hali sartaroshlar yo'q</div>
                <p>Yangi sartarosh qo'shish uchun yuqoridagi "Yangi sartarosh" tugmasini bosing</p>
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
                        <th>Ism</th>
                        <th>Telefon</th>
                        <th>Ish vaqti</th>
                        <th>Kategoriya</th>
                        <th>Holat</th>
                        <th>Bot</th>
                        <th>Harakatlar</th>
                    </tr>
                </thead>
                <tbody>
                    ${barbers.map(barber => {
                        const isRunning = botStatuses[barber.id] === true;
                        return `
                        <tr>
                            <td>${barber.id}</td>
                            <td>
                                <strong>${barber.name}</strong>
                            </td>
                            <td>${barber.phone || '-'}</td>
                            <td>${barber.work_start} - ${barber.work_end}</td>
                            <td>
                                <span class="badge badge-info">
                                    ${barber.gender_category === 'male' ? 'Erkak' :
                                      barber.gender_category === 'female' ? 'Ayol' : 'Ikkala jins'}
                                </span>
                            </td>
                            <td>
                                <span class="badge ${barber.is_active ? 'badge-success' : 'badge-danger'}">
                                    ${barber.is_active ? 'Faol' : 'Nofaol'}
                                </span>
                            </td>
                            <td>
                                ${isRunning
                                    ? `<span class="badge badge-success">Ishlayapti</span>
                                       <button onclick="toggleBot(${barber.id}, 'stop')" class="btn btn-danger btn-sm" style="margin-left:4px;">Stop</button>`
                                    : `<span class="badge badge-danger">To'xtagan</span>
                                       <button onclick="toggleBot(${barber.id}, 'start')" class="btn btn-primary btn-sm" style="margin-left:4px;">Start</button>`
                                }
                            </td>
                            <td>
                                <button onclick="editBarber(${barber.id})" class="btn btn-secondary btn-sm">
                                    ✏️ Tahrirlash
                                </button>
                                <button onclick="deleteBarber(${barber.id})" class="btn btn-danger btn-sm">
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

// Open modal for adding new barber
function openAddModal() {
    editingBarberId = null;
    document.getElementById('modalTitle').textContent = 'Yangi sartarosh qo\'shish';
    document.getElementById('barberForm').reset();
    document.getElementById('barberModal').classList.add('active');
}

// Open modal for editing barber
async function editBarber(id) {
    try {
        editingBarberId = id;
        const barber = barbers.find(b => b.id === id);

        if (!barber) {
            throw new Error('Sartarosh topilmadi');
        }

        document.getElementById('modalTitle').textContent = 'Sartaroshni tahrirlash';
        document.getElementById('barberName').value = barber.name;
        document.getElementById('barberToken').value = barber.bot_token;
        document.getElementById('barberAdminTgId').value = barber.admin_telegram_id || '';
        document.getElementById('barberPhone').value = barber.phone || '';
        document.getElementById('barberImageUrl').value = barber.image_url || '';
        document.getElementById('barberWorkStart').value = barber.work_start;
        document.getElementById('barberWorkEnd').value = barber.work_end;
        document.getElementById('barberGender').value = barber.gender_category;
        document.getElementById('barberIsActive').checked = barber.is_active;

        document.getElementById('barberModal').classList.add('active');
    } catch (error) {
        console.error('Error loading barber:', error);
        showNotification('Sartaroshni yuklashda xatolik', 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('barberModal').classList.remove('active');
    editingBarberId = null;
}

// Save barber (create or update)
async function saveBarber(event) {
    event.preventDefault();

    const formData = {
        name: document.getElementById('barberName').value,
        bot_token: document.getElementById('barberToken').value,
        admin_telegram_id: document.getElementById('barberAdminTgId').value || null,
        phone: document.getElementById('barberPhone').value || null,
        image_url: document.getElementById('barberImageUrl').value || null,
        work_start: document.getElementById('barberWorkStart').value,
        work_end: document.getElementById('barberWorkEnd').value,
        gender_category: document.getElementById('barberGender').value,
        is_active: document.getElementById('barberIsActive').checked,
    };

    try {
        if (editingBarberId) {
            // Update existing barber
            await API.updateBarber(editingBarberId, formData);
            showNotification('Sartarosh muvaffaqiyatli yangilandi!', 'success');
        } else {
            // Create new barber
            await API.createBarber(formData);
            showNotification('Sartarosh muvaffaqiyatli qo\'shildi!', 'success');
        }

        closeModal();
        loadBarbers();
    } catch (error) {
        console.error('Error saving barber:', error);
        showNotification(error.message || 'Xatolik yuz berdi', 'error');
    }
}

// Delete barber
async function deleteBarber(id) {
    const barber = barbers.find(b => b.id === id);

    if (!confirm(`"${barber.name}" sartaroshni o'chirmoqchimisiz?`)) {
        return;
    }

    try {
        await API.deleteBarber(id);
        showNotification('Sartarosh muvaffaqiyatli o\'chirildi!', 'success');
        loadBarbers();
    } catch (error) {
        console.error('Error deleting barber:', error);
        showNotification(error.message || 'O\'chirishda xatolik', 'error');
    }
}

// Toggle bot start/stop
async function toggleBot(barberId, action) {
    try {
        const result = await API.request(`/api/bots/${barberId}/${action}`, {
            method: 'POST'
        });
        showNotification(result.message, 'success');
        loadBarbers();
    } catch (error) {
        console.error(`Error ${action} bot:`, error);
        showNotification(error.message || `Bot ${action} xatolik`, 'error');
    }
}

// Restart all bots
async function restartAllBots() {
    if (!confirm('Barcha botlarni qayta ishga tushirmoqchimisiz?')) return;

    try {
        const result = await API.request('/api/bots/restart-all', { method: 'POST' });
        showNotification(result.message, 'success');
        loadBarbers();
    } catch (error) {
        console.error('Error restarting bots:', error);
        showNotification(error.message || 'Qayta ishga tushirishda xatolik', 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadBarbers();

    document.getElementById('barberForm').addEventListener('submit', saveBarber);
});
