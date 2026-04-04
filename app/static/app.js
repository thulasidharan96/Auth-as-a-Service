const API_URL = '/api/v1';

let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

// Utility to handle API calls
async function fetchApi(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    if (accessToken) options.headers['Authorization'] = `Bearer ${accessToken}`;
    if (options.body && typeof options.body === 'object') {
        if (!(options.body instanceof FormData)) {
            options.body = JSON.stringify(options.body);
            options.headers['Content-Type'] = 'application/json';
        }
    }
    
    let res = await fetch(`${API_URL}${endpoint}`, options);
    if (res.status === 401 && refreshToken) {
        // Try refresh
        const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (refreshRes.ok) {
            const data = await refreshRes.json();
            setTokens(data);
            options.headers['Authorization'] = `Bearer ${accessToken}`;
            res = await fetch(`${API_URL}${endpoint}`, options);
        } else {
            logout();
        }
    }
    return res;
}

function setTokens(data) {
    accessToken = data.access_token;
    refreshToken = data.refresh_token;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    checkAuth();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    accessToken = null;
    refreshToken = null;
    checkAuth();
}

function showAlert(id, message, isError = false) {
    const el = document.getElementById(id);
    el.textContent = message;
    el.className = `alert ${isError ? 'error' : 'success'}`;
    setTimeout(() => el.classList.add('hidden'), 5000);
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active-form'));
    document.querySelector(`.tab-btn[onclick="switchTab('${tab}')"]`).classList.add('active');
    document.getElementById(`${tab}-form`).classList.add('active-form');
}

async function checkAuth() {
    if (!accessToken) {
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('dashboard-section').classList.add('hidden');
        document.getElementById('status-bar').style.display = 'none';
        return;
    }
    
    const res = await fetchApi('/auth/me');
    if (res.ok) {
        const user = await res.json();
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('dashboard-section').classList.remove('hidden');
        document.getElementById('status-bar').style.display = 'flex';
        document.getElementById('user-email').textContent = user.email;
        document.getElementById('user-id').textContent = `ID: ${user.id}`;
        fetchSessions();
        fetchApiKeys();
    } else {
        logout();
    }
}

// Auth Flows
async function loginWithPassword() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const formData = new FormData();
    formData.append('username', email); // OAuth2PasswordRequestForm needs username
    formData.append('password', password);
    
    const res = await fetchApi('/auth/login', { method: 'POST', body: formData });
    if (res.ok) {
        setTokens(await res.json());
    } else {
        showAlert('auth-alert', 'Invalid credentials', true);
    }
}

async function registerUser() {
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const res = await fetchApi('/auth/register', {
        method: 'POST',
        body: { email, password }
    });
    if (res.ok) {
        showAlert('auth-alert', 'Registration successful! Please login.');
        switchTab('login');
    } else {
        const err = await res.json();
        showAlert('auth-alert', err.detail || 'Registration failed', true);
    }
}

async function sendMagicLink() {
    const email = document.getElementById('magic-email').value;
    if (!email) return showAlert('auth-alert', 'Enter email', true);
    const res = await fetchApi(`/auth/magic-link?email=${encodeURIComponent(email)}`, { method: 'POST' });
    if (res.ok) showAlert('auth-alert', 'Magic Link Sent to console logs!');
    else showAlert('auth-alert', 'Failed to send link', true);
}

// WebAuthn
async function registerPasskey() {
    try {
        const res = await fetchApi('/auth/webauthn/register/start', { method: 'POST' });
        const options = await res.json();
        
        // Use SimpleWebAuthn
        const { startRegistration } = SimpleWebAuthnBrowser;
        const attResp = await startRegistration(options);
        
        const finishRes = await fetchApi('/auth/webauthn/register/finish', {
            method: 'POST',
            body: { response: attResp }
        });
        
        if (finishRes.ok) showAlert('dash-alert', 'Passkey Registered!');
        else showAlert('dash-alert', 'Passkey registration failed', true);
    } catch (e) {
        showAlert('dash-alert', e.message, true);
    }
}

async function webauthnLogin() {
    try {
        const email = document.getElementById('login-email').value;
        if (!email) return showAlert('auth-alert', 'Enter email first to find passkey', true);
        
        const res = await fetchApi('/auth/webauthn/login/start', { 
            method: 'POST',
            body: { email } 
        });
        if(!res.ok) throw new Error('User not found or no passkey configured');
        const options = await res.json();
        
        const { startAuthentication } = SimpleWebAuthnBrowser;
        const asseResp = await startAuthentication(options);
        
        const finishRes = await fetchApi('/auth/webauthn/login/finish', {
            method: 'POST',
            body: { email, response: asseResp }
        });
        
        if (finishRes.ok) setTokens(await finishRes.json());
        else showAlert('auth-alert', 'Passkey login failed', true);
    } catch (e) {
        showAlert('auth-alert', e.message, true);
    }
}

// API Keys
async function fetchApiKeys() {
    const res = await fetchApi('/apikeys/');
    if (!res.ok) return;
    const keys = await res.json();
    const container = document.getElementById('api-keys-list');
    container.innerHTML = keys.map(k => `
        <div class="list-item">
            <span>${k.name}</span>
            <button onclick="revokeApiKey('${k.id}')" class="btn-small">Revoke</button>
        </div>
    `).join('');
}

async function createApiKey() {
    const name = document.getElementById('api-key-name').value;
    if (!name) return showAlert('dash-alert', 'Enter a key name', true);
    
    // Explicitly send empty scopes to avoid generic 422 if model forces it
    const res = await fetchApi('/apikeys/', {
        method: 'POST',
        body: { name: name, scopes: [] }
    });
    
    if (res.ok) {
        const data = await res.json();
        document.getElementById('modal-api-key').textContent = data.raw_key;
        document.getElementById('api-modal').classList.remove('hidden');
        fetchApiKeys();
        document.getElementById('api-key-name').value = '';
    } else {
        const err = await res.json();
        console.error(err);
        showAlert('dash-alert', err.detail || 'Failed to create key', true);
    }
}

async function revokeApiKey(id) {
    await fetchApi(`/apikeys/${id}`, { method: 'DELETE' });
    fetchApiKeys();
}

function closeModal() {
    document.getElementById('api-modal').classList.add('hidden');
}

// OTP
async function setupOTP() {
    const res = await fetchApi('/auth/setup-otp', { method: 'POST' });
    if (res.ok) {
        const data = await res.json();
        document.getElementById('otp-verify-area').classList.remove('hidden');
        document.getElementById('otp-uri').textContent = data.otp_uri;
    }
}

async function verifyOTP() {
    const code = document.getElementById('otp-code').value;
    const res = await fetchApi('/auth/verify-otp', {
        method: 'POST',
        body: { code }
    });
    if (res.ok) {
        showAlert('dash-alert', 'OTP Setup Validated!');
        document.getElementById('otp-verify-area').classList.add('hidden');
    } else {
        showAlert('dash-alert', 'Invalid code', true);
    }
}

// Sessions
async function fetchSessions() {
    const res = await fetchApi('/sessions/');
    if (!res.ok) return;
    const sessions = await res.json();
    const container = document.getElementById('sessions-list');
    container.innerHTML = sessions.map(s => `
        <div class="list-item">
            <div>
                <div>${s.device_info || 'Unknown Device'}</div>
                <div class="text-sm text-dim">${s.ip_address || 'Unknown IP'}</div>
            </div>
            ${s.is_revoked ? '<span class="text-error">Revoked</span>' : `<button onclick="revokeSession('${s.id}')" class="btn-small">Revoke</button>`}
        </div>
    `).join('');
}

async function revokeSession(id) {
    await fetchApi(`/sessions/${id}`, { method: 'DELETE' });
    fetchSessions();
}

// Init
checkAuth();
