const BASE_URL = 'http://127.0.0.1:8000/api';


function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
}

function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}

function getHeaders() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

function getHeadersWithCSRF() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

function handleResponse(response) {
    return response.json().then(data => {
        if (!response.ok) {
            const errorMessage = data.error || data.detail || data.message || 'خطا در ارتباط با سرور';
            throw new Error(errorMessage);
        }
        return data;
    });
}

function getFormDataHeaders() {
    const token = getToken();
    return {
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}


const AuthAPI = {
    register: async (formData) => {
        const response = await fetch(`${BASE_URL}/users/register/`, {
            method: 'POST',
            body: formData
        });
        return handleResponse(response);
    },

    login: async (username, password) => {
        const response = await fetch(`${BASE_URL}/users/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()  
            },
            credentials: 'include',  
            body: JSON.stringify({ username, password })
        });

        const data = await handleResponse(response);
        
        if (data.access) {
            setToken(data.access);
            localStorage.setItem('userRole', data.user?.role || 'customer');
            localStorage.setItem('username', data.user?.username || username);
            localStorage.setItem('userId', data.user?.id || '');
        }
        
        return { 
            role: data.user?.role || 'customer',
            user: data.user
        };
    },

    logout: () => {
        removeToken();
        window.location.href = '/';
    },

    changePassword: async (oldPassword, newPassword, confirmPassword) => {
        if (newPassword !== confirmPassword) {
            throw new Error('رمز جدید و تکرار آن مطابقت ندارند');
        }
        if (newPassword.length < 6) {
            throw new Error('رمز عبور باید حداقل ۶ کاراکتر باشد');
        }

        const response = await fetch(`${BASE_URL}/users/change_password/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword,
                confirm_new_password: confirmPassword
            })
        });
        return handleResponse(response);
    },

    getProfile: async () => {
        const response = await fetch(`${BASE_URL}/users/me/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    updateProfile: async (formData) => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/users/update_me/`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        const data = await handleResponse(response);
        if (data.user?.username) {
            localStorage.setItem('username', data.user.username);
        }
        return data;
    }
};


const AdminAPI = {
    getDashboardData: async () => {
        const response = await fetch(`${BASE_URL}/users/admin_stats/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getUsers: async () => {
        const response = await fetch(`${BASE_URL}/users/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    createUser: async (userData) => {
        console.log('📤 داده‌های ارسالی برای ایجاد کاربر:', userData);
        try {
            const response = await fetch(`${BASE_URL}/users/`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(userData)
            });
            const data = await response.json();
            console.log('📥 پاسخ از سرور:', data);
            if (!response.ok) {
                throw new Error(data.error || data.detail || JSON.stringify(data));
            }
            return data;
        } catch (error) {
            console.error('❌ خطا در createUser:', error);
            throw error;
        }
    },

    updateUser: async (userId, userData) => {
        console.log('📤 داده‌های ارسالی برای ویرایش کاربر:', userData);
    
        // فیلدهای خالی رو حذف کن
        const cleanData = {};
        for (const key in userData) {
            if (userData[key] !== undefined && userData[key] !== null && userData[key] !== '') {
                cleanData[key] = userData[key];
            }
        }
    
        const response = await fetch(`${BASE_URL}/users/${userId}/`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify(cleanData)
        });
    
        const data = await response.json();
        console.log('📥 پاسخ ویرایش:', data);
    
        if (!response.ok) {
            throw new Error(data.error || data.detail || 'خطا در ویرایش کاربر');
        }
        return data;
    },

    deleteUser: async (userId) => {
        const response = await fetch(`${BASE_URL}/users/${userId}/`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || data.detail || 'خطا در حذف کاربر');
        }
        return true;
    },

    getServices: async () => {
        const response = await fetch(`${BASE_URL}/services/services/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    toggleServiceStatus: async (serviceId) => {
        const response = await fetch(`${BASE_URL}/services/services/${serviceId}/`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify({ is_active: true })
        });
        return handleResponse(response);
    },

    getBookings: async () => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    forceApprove: async (bookingId) => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/confirm/`, {
            method: 'POST',
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    forceCancel: async (bookingId) => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/cancel/`, {
            method: 'POST',
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getBookingsStats: async () => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/stats/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    exportCustomerBookingsPDF: async () => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/bookings/bookings/export_customer_pdf/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('خطا در تولید PDF');
        return response.blob();
    },

    exportProviderBookingsPDF: async () => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/bookings/bookings/export_provider_pdf/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('خطا در تولید PDF');
        return response.blob();
    },

    exportAdminStatsPDF: async () => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/bookings/bookings/export_admin_stats_pdf/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('خطا در تولید PDF');
        return response.blob();
    },

    exportInvoicePDF: async (bookingId) => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/export_invoice_pdf/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('خطا در تولید فاکتور');
        return response.blob();
    }
};


const ProviderAPI = {
    getMyServices: async () => {
        const response = await fetch(`${BASE_URL}/services/services/my_services/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    createService: async (formData) => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/services/services/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        return handleResponse(response);
    },

    updateService: async (serviceId, formData) => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/services/services/${serviceId}/`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        return handleResponse(response);
    },

    deleteService: async (serviceId) => {
        const response = await fetch(`${BASE_URL}/services/services/${serviceId}/`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || data.detail || 'خطا در حذف سرویس');
        }
        return true;
    },

    getTimeSlots: async (serviceId) => {
        console.log('📤 دریافت زمان‌بندی برای سرویس:', serviceId);
        const response = await fetch(`${BASE_URL}/services/time-slots/?service=${serviceId}`, {
            method: 'GET',  
            headers: getHeaders()
        });
        const data = await response.json();
        console.log('📥 پاسخ زمان‌بندی:', data);
    
        if (data.results) {
            return data.results;
        } else if (Array.isArray(data)) {
            return data;
        } else {
            return [];
        }
    },

    addTimeSlot: async (serviceId, slotData) => {
        console.log('📤 ارسال زمان‌بندی:', { serviceId, slotData });
        
        const payload = {
            service: serviceId,
            start_time: slotData.start_time,
            end_time: slotData.end_time,
            is_active: slotData.is_active !== undefined ? slotData.is_active : true
        };
    
        console.log('📤 payload نهایی:', payload);
    
        const response = await fetch(`${BASE_URL}/services/time-slots/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(payload)
        });
    
        const data = await response.json();
        console.log('📥 پاسخ:', data);
    
        if (!response.ok) {
            throw new Error(data.error || data.detail || data.message || 'خطا در افزودن زمان');
        }
        return data;
    },

    deleteTimeSlot: async (slotId) => {
        const response = await fetch(`${BASE_URL}/services/time-slots/${slotId}/delete_if_not_booked/`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || data.detail || 'خطا در حذف زمان');
        }
        return true;
    },

    toggleTimeSlotActive: async (slotId) => {
        const response = await fetch(`${BASE_URL}/services/time-slots/${slotId}/toggle_active/`, {
            method: 'POST',
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getMyBookings: async () => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/my_bookings/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    updateBookingStatus: async (bookingId, status) => {
        const endpoint = status === 'confirmed' ? 'confirm' : 'reject';
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/${endpoint}/`, {
            method: 'POST',
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getMyRevenue: async () => {
        const response = await fetch(`${BASE_URL}/users/provider_stats/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getMyReviews: async () => {
        const response = await fetch(`${BASE_URL}/services/reviews/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    }
};


const CustomerAPI = {
    searchServices: async (filters) => {
        const query = new URLSearchParams();
        if (filters.q) query.append('search', filters.q);
        if (filters.category && filters.category !== 'all') query.append('category', filters.category);
        if (filters.min_price) query.append('min_price', filters.min_price);
        if (filters.max_price) query.append('max_price', filters.max_price);
    
        const url = query.toString() 
            ? `${BASE_URL}/services/services/?${query.toString()}`
            : `${BASE_URL}/services/services/`;
    
        console.log('📤 آدرس جستجو:', url);
    
        const response = await fetch(url, {
            headers: getHeaders()
        });
        const data = await response.json();
        console.log('📥 پاسخ جستجو:', data);
    
        if (data.results) {
            return data.results;
        } else if (Array.isArray(data)) {
            return data;
        } else {
            return [];
        }
    },

    getServiceTimeSlots: async (serviceId, date) => {
        const url = `${BASE_URL}/services/services/${serviceId}/available_slots/`;
        const response = await fetch(url, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    createBooking: async (bookingData) => {
        const token = getToken();
        if (!token) {
            throw new Error('لطفاً ابتدا وارد حساب کاربری خود شوید');
        }
        
        const response = await fetch(`${BASE_URL}/bookings/bookings/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                time_slot: bookingData.slotId,
                customer_note: bookingData.note || ''
            })
        });
        
        // ===== بررسی خطای 403 =====
        if (response.status === 403) {
            throw new Error('شما اجازه انجام این دستور را ندارید. لطفاً دوباره وارد شوید.');
        }
        
        return handleResponse(response);
    },

    getMyBookings: async () => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/my_bookings/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    cancelBooking: async (bookingId) => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/cancel/`, {
            method: 'POST',
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getCancelInfo: async (bookingId) => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/cancel_info/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getPaymentInfo: async (bookingId) => {
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/payment_info/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    createPayment: async (bookingId, cardNumber, cardHolderName) => {
        const response = await fetch(`${BASE_URL}/bookings/payments/create_payment/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                booking: bookingId,
                card_number: cardNumber,
                card_holder_name: cardHolderName
            })
        });
        return handleResponse(response);
    },

    addReview: async (bookingId, rating, comment) => {
        const response = await fetch(`${BASE_URL}/services/reviews/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                booking: bookingId,
                rating: rating,
                comment: comment
            })
        });
        return handleResponse(response);
    },

    getCustomerStats: async () => {
        const response = await fetch(`${BASE_URL}/users/customer_stats/`, {
            headers: getHeaders()
        });
        return handleResponse(response);
    },

    getInvoicePDF: async (bookingId) => {
        const token = getToken();
        const response = await fetch(`${BASE_URL}/bookings/bookings/${bookingId}/export_invoice_pdf/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('خطا در تولید فاکتور');
        return response.blob();
    }
};


window.showError = function(message) {
    removeAlerts();
    const alert = document.createElement('div');
    alert.className = 'custom-alert custom-alert-error';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
};

window.showSuccess = function(message) {
    removeAlerts();
    const alert = document.createElement('div');
    alert.className = 'custom-alert custom-alert-success';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
};

function removeAlerts() {
    document.querySelectorAll('.custom-alert').forEach(a => a.remove());
}
window.AuthAPI = AuthAPI;
window.AdminAPI = AdminAPI;
window.ProviderAPI = ProviderAPI;
window.CustomerAPI = CustomerAPI;