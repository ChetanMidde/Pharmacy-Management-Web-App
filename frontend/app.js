// Global State
const state = {
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
    medicines: [],
    cart: [],
    wishlist: JSON.parse(localStorage.getItem('wishlist') || '[]'),
    selectedRxMed: null,
    storeConditionFilter: null
};

const API_BASE = 'http://localhost:8000';

// Utilities
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast fade-in ${type}`;
    
    let icon = 'information-circle-outline';
    if(type === 'success') icon = 'checkmark-circle-outline';
    if(type === 'error') icon = 'alert-circle-outline';
    
    toast.innerHTML = `<ion-icon name="${icon}"></ion-icon> <span>${message}</span>`;
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function apiFetch(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    if (state.token) {
        options.headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (response.status === 401) {
        logout();
        throw new Error("Unauthorized");
    }
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "API Error");
    }
    return data;
}

// Initialization & Routing
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        initApp();
    } else {
        document.getElementById('login-screen').classList.remove('hidden');
    }
    
    setupEventListeners();
});

function initApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    
    document.getElementById('user-name-display').innerText = "Logged In";
    document.getElementById('user-role-display').innerText = state.role || "User";
    
    loadDashboard();
    fetchMedicines();
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    state.token = null;
    state.role = null;
    document.getElementById('app-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('hidden');
    showToast('Logged out successfully');
}

// Event Listeners
function setupEventListeners() {
    // Auth
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const u = document.getElementById('username').value;
        const p = document.getElementById('password').value;
        const btn = e.target.querySelector('button');
        btn.innerText = 'Signing in...';
        
        try {
            const formData = new URLSearchParams();
            formData.append('username', u);
            formData.append('password', p);
            
            const res = await fetch(`${API_BASE}/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Login failed');
            
            state.token = data.access_token;
            state.role = data.role;
            localStorage.setItem('token', state.token);
            localStorage.setItem('role', state.role);
            
            initApp();
            showToast('Logic successful', 'success');
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            btn.innerText = 'Sign In';
        }
    });

    document.getElementById('logout-btn').addEventListener('click', logout);

    // Navigation Tab Switching
    document.querySelectorAll('.nav-menu .nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-menu .nav-item').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            document.getElementById(targetId).classList.remove('hidden');
            
            if(targetId === 'dashboard-tab') loadDashboard();
            if(targetId === 'pos-tab' || targetId === 'inventory-tab') fetchMedicines();
            if(targetId === 'store-tab') {
                fetchMedicines().then(() => {
                    renderStoreConditions();
                    renderStoreProducts();
                    renderWishlist();
                });
            }
        });
    });

    // POS Search
    document.getElementById('pos-search').addEventListener('input', (e) => {
        renderPOSProducts(e.target.value);
    });

    // POS Checkout
    document.getElementById('checkout-btn').addEventListener('click', processCheckout);
    document.getElementById('store-buy-now-btn').addEventListener('click', processCheckout);

    // Modals
    document.getElementById('btn-add-medicine').addEventListener('click', () => {
        if(state.role === 'staff') {
            showToast('Staff cannot add inventory', 'error');
            return;
        }
        document.getElementById('add-med-modal').classList.remove('hidden');
    });
    
    document.getElementById('btn-close-add-med').addEventListener('click', () => {
        document.getElementById('add-med-modal').classList.add('hidden');
    });

    document.getElementById('add-med-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            const payload = {
                name: document.getElementById('med-name').value,
                description: document.getElementById('med-desc').value,
                is_controlled: document.getElementById('med-controlled').checked,
                stock: parseInt(document.getElementById('med-stock').value),
                price: parseFloat(document.getElementById('med-price').value),
                expiry_date: document.getElementById('med-expiry').value
            };
            
            await apiFetch('/api/medicines', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            showToast('Medicine added', 'success');
            document.getElementById('add-med-modal').classList.add('hidden');
            e.target.reset();
            fetchMedicines();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Rx Modal
    document.getElementById('btn-cancel-rx').addEventListener('click', () => {
        document.getElementById('rx-modal').classList.add('hidden');
        state.selectedRxMed = null;
    });

    document.getElementById('btn-submit-rx').addEventListener('click', () => {
        const rx = document.getElementById('rx-details').value;
        if (!rx) return showToast('Details required', 'error');
        
        addToCart(state.selectedRxMed, rx);
        document.getElementById('rx-modal').classList.add('hidden');
        document.getElementById('rx-details').value = '';
        state.selectedRxMed = null;
    });

    // AI
    document.getElementById('btn-run-ai').addEventListener('click', runAIPrediction);
}


// --- API Integrations & Renderers ---

async function loadDashboard() {
    try {
        const stats = await apiFetch('/api/dashboard/stats');
        
        // Counter Animation
        animateCount('stat-sales', stats.total_sales);
        animateCount('stat-low-stock', stats.low_stock_items);
        animateCount('stat-controlled', stats.controlled_drug_dispensed);
        
    } catch (e) {
        // likely restricted scope
        document.getElementById('stat-sales').innerText = '-';
    }
}

function animateCount(id, target) {
    const el = document.getElementById(id);
    let current = 0;
    const incr = Math.max(1, Math.ceil(target / 20));
    const timer = setInterval(() => {
        current += incr;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.innerText = current.toString();
    }, 40);
}

async function fetchMedicines() {
    try {
        state.medicines = await apiFetch('/api/medicines');
        renderPOSProducts();
        renderInventoryTable();
    } catch (e) {
        showToast('Failed to fetch catalog', 'error');
    }
}

function renderInventoryTable() {
    const tbody = document.getElementById('inventory-table-body');
    if(!tbody) return;
    
    tbody.innerHTML = '';
    state.medicines.forEach(m => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${m.name}</strong> <br><small style="color:var(--text-muted)">Exp: ${m.expiry_date}</small></td>
            <td>${m.stock < 10 ? `<span style="color:var(--danger); font-weight:700;">${m.stock} (Low)</span>` : m.stock}</td>
            <td>₹${m.price.toFixed(2)}</td>
            <td>${m.is_controlled ? '<span class="badge badge-danger">Restricted</span>' : 'Standard'}</td>
            <td>${m.stock > 0 ? `<span style="color:var(--success)">Available</span>` : `<span style="color:var(--danger)">Out of Stock</span>`}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderPOSProducts(filter = '') {
    const grid = document.getElementById('pos-product-grid');
    if(!grid) return;
    
    grid.innerHTML = '';
    const filtered = state.medicines.filter(m => m.name.toLowerCase().includes(filter.toLowerCase()));
    
    filtered.forEach(m => {
        const div = document.createElement('div');
        div.className = 'product-card';
        div.innerHTML = `
            <div>
                <div class="product-name">${m.name}</div>
                <div class="product-stock" style="font-size:0.8rem; color: ${m.stock < 10 ? 'var(--danger)' : 'var(--text-muted)'}">Stock: ${m.stock}</div>
                ${m.is_controlled ? '<div class="badge badge-danger mt-1">Rx Req</div>' : ''}
            </div>
            <div class="flex-between mt-1" style="align-items:flex-end;">
                <div class="product-price">₹${m.price.toFixed(2)}</div>
                <button class="btn btn-primary" style="padding:0.4rem; border-radius:8px;" ${m.stock <= 0 ? 'disabled' : ''}>
                    <ion-icon name="add-outline" style="margin:0"></ion-icon>
                </button>
            </div>
        `;
        
        div.querySelector('button').addEventListener('click', () => {
            if (m.is_controlled) {
                state.selectedRxMed = m;
                document.getElementById('rx-med-name').innerText = m.name;
                document.getElementById('rx-modal').classList.remove('hidden');
            } else {
                addToCart(m);
            }
        });
        
        grid.appendChild(div);
    });
}

function addToCart(medicine, rxInfo = null) {
    const existing = state.cart.find(i => i.id === medicine.id);
    
    if (existing) {
        if (existing.qty >= medicine.stock) {
            showToast('Not enough stock', 'warning');
            return;
        }
        existing.qty++;
    } else {
        state.cart.push({ ...medicine, qty: 1, rx: rxInfo });
    }
    
    renderCart();
}

function renderCart() {
    const container1 = document.getElementById('cart-items');
    const container2 = document.getElementById('store-cart-items');
    const btn1 = document.getElementById('checkout-btn');
    const btn2 = document.getElementById('store-buy-now-btn');
    
    let total = 0;
    let htmlStr = '';
    
    if (state.cart.length === 0) {
        htmlStr = '<p class="empty-cart-msg">Cart is empty</p>';
        if(btn1) btn1.disabled = true;
        if(btn2) btn2.disabled = true;
    } else {
        state.cart.forEach((item, index) => {
            total += item.price * item.qty;
            htmlStr += `
                <div class="cart-item fade-in">
                    <div class="cart-item-info">
                        <strong>${item.name}</strong>
                        <span>₹${item.price.toFixed(2)} x ${item.qty} ${item.rx ? '<br>Rx: ' + item.rx : ''}</span>
                    </div>
                    <div class="cart-item-qty">
                        <button class="qty-btn" onclick="updateCartQty(${index}, -1)">-</button>
                        <span>${item.qty}</span>
                        <button class="qty-btn" onclick="updateCartQty(${index}, 1)">+</button>
                    </div>
                </div>
            `;
        });
        if(btn1) btn1.disabled = false;
        if(btn2) btn2.disabled = false;
    }
    
    if(container1) container1.innerHTML = htmlStr;
    if(container2) container2.innerHTML = htmlStr;
    
    const formattedTotal = `₹${total.toFixed(2)}`;
    if(document.getElementById('cart-subtotal')) document.getElementById('cart-subtotal').innerText = formattedTotal;
    if(document.getElementById('cart-total')) document.getElementById('cart-total').innerText = formattedTotal;
    if(document.getElementById('store-cart-total')) document.getElementById('store-cart-total').innerText = formattedTotal;
}

window.updateCartQty = function(index, delta) {
    const item = state.cart[index];
    const med = state.medicines.find(m => m.id === item.id);
    
    const newQty = item.qty + delta;
    if (newQty <= 0) {
        state.cart.splice(index, 1);
    } else if (newQty > med.stock) {
        showToast('Max stock limit reached', 'warning');
    } else {
        item.qty = newQty;
    }
    renderCart();
};

async function processCheckout() {
    if (state.cart.length === 0) return;
    const btn = document.getElementById('checkout-btn');
    btn.disabled = true;
    btn.innerHTML = '<ion-icon name="sync-outline" class="spin"></ion-icon> Processing...';
    
    try {
        const payload = {
            items: state.cart.map(i => ({
                medicine_id: i.id,
                quantity: i.qty,
                prescription_info: i.rx
            }))
        };
        
        const res = await apiFetch('/api/sales', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        showToast(`Transaction complete! Total: ₹${res.total.toFixed(2)}`, 'success');
        state.cart = [];
        renderCart();
        fetchMedicines(); // update stock
        loadDashboard(); // update stats
        
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.innerHTML = 'Process Transaction';
        btn.disabled = state.cart.length === 0;
    }
}

// AI Feature
async function runAIPrediction() {
    const btn = document.getElementById('btn-run-ai');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<ion-icon name="sync-outline"></ion-icon> Analyzing Vectors...';
    btn.disabled = true;
    
    const grid = document.getElementById('ai-results-grid');
    grid.innerHTML = '<div class="glass-card full-center text-center grid-span-2">Calculating machine learning demand models...</div>';
    
    try {
        const resp = await apiFetch('/api/ai/predict-demand');
        
        grid.innerHTML = '';
        
        resp.ai_insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'glass-card fade-in-up';
            card.innerHTML = `
                <div class="ai-med-name">${insight.name}</div>
                <div class="mt-1" style="color:var(--text-muted)">Current Stock: ${insight.current_stock}</div>
                <div class="ai-prediction">${insight.predicted_demand_next_month} <span style="font-size:1rem; font-weight:normal; color:var(--text-muted)">units projected</span></div>
                <div class="ai-severity severity-${insight.severity}">${insight.recommendation}</div>
                <div class="ai-reason mt-1">${insight.reasoning}</div>
            `;
            grid.appendChild(card);
        });
        
        showToast('AI Analysis Complete', 'success');
        
    } catch (e) {
        showToast('AI Model Service endpoint failed', 'error');
        grid.innerHTML = '<div class="glass-card full-center text-center grid-span-2" style="color:var(--danger)">Analysis failed. Please check permissions.</div>';
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// --- Health Store logic ---
function renderStoreConditions() {
    const container = document.getElementById('conditions-filter-container');
    if(!container) return;
    
    // Extract unique conditions
    const conditions = [...new Set(state.medicines.map(m => m.condition || 'General Health'))];
    
    container.innerHTML = `
        <button class="badge ${!state.storeConditionFilter ? 'badge-primary' : ''}" 
            style="padding:0.5rem 1rem; cursor:pointer;" 
            onclick="setStoreFilter(null)">All Conditions</button>
    `;
    
    conditions.forEach(cond => {
        const isActive = state.storeConditionFilter === cond;
        container.innerHTML += `
            <button class="badge ${isActive ? 'badge-primary' : ''}" 
                style="padding:0.5rem 1rem; cursor:pointer; background: ${isActive ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}" 
                onclick="setStoreFilter('${cond}')">${cond}</button>
        `;
    });
}

window.setStoreFilter = function(cond) {
    state.storeConditionFilter = cond;
    renderStoreConditions();
    renderStoreProducts();
};

function renderStoreProducts() {
    const grid = document.getElementById('store-product-grid');
    const title = document.getElementById('store-current-condition');
    if(!grid) return;
    
    title.innerText = state.storeConditionFilter ? `Showing: ${state.storeConditionFilter}` : "All Products";
    
    grid.innerHTML = '';
    const filtered = state.storeConditionFilter 
        ? state.medicines.filter(m => m.condition === state.storeConditionFilter)
        : state.medicines;
        
    filtered.forEach(m => {
        const inWishlist = state.wishlist.some(w => w.id === m.id);
        
        const div = document.createElement('div');
        div.className = 'product-card';
        div.innerHTML = `
            <div>
                <div class="flex-between">
                    <div class="product-name">${m.name}</div>
                    <ion-icon name="${inWishlist ? 'heart' : 'heart-outline'}" 
                        style="color:var(--danger); cursor:pointer; font-size:1.2rem;" 
                        onclick="toggleWishlist(${m.id})"></ion-icon>
                </div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.5rem;">${m.description}</div>
                <div class="product-stock" style="font-size:0.8rem; color: ${m.stock < 10 ? 'var(--danger)' : 'var(--text-muted)'}">Stock: ${m.stock}</div>
                ${m.is_controlled ? '<div class="badge badge-danger mt-1">Rx Req</div>' : ''}
            </div>
            <div class="flex-between mt-1" style="align-items:flex-end;">
                <div class="product-price">₹${m.price.toFixed(2)}</div>
                <button class="btn btn-primary" style="padding:0.4rem; border-radius:8px;" ${m.stock <= 0 ? 'disabled' : ''}>
                    <ion-icon name="cart-outline" style="margin:0"></ion-icon> Add to Cart
                </button>
            </div>
        `;
        
        div.querySelector('.btn-primary').addEventListener('click', () => {
            if (m.is_controlled) {
                state.selectedRxMed = m;
                document.getElementById('rx-med-name').innerText = m.name;
                document.getElementById('rx-modal').classList.remove('hidden');
            } else {
                addToCart(m);
                showToast('Added to Cart', 'success');
            }
        });
        
        grid.appendChild(div);
    });
}

window.toggleWishlist = function(id) {
    const exists = state.wishlist.findIndex(w => w.id === id);
    if(exists >= 0) {
        state.wishlist.splice(exists, 1);
        showToast('Removed from Wishlist', 'info');
    } else {
        const med = state.medicines.find(m => m.id === id);
        if(med) state.wishlist.push(med);
        showToast('Added to Wishlist', 'success');
    }
    localStorage.setItem('wishlist', JSON.stringify(state.wishlist));
    renderStoreProducts();
    renderWishlist();
};

function renderWishlist() {
    const container = document.getElementById('wishlist-container');
    if(!container) return;
    
    if(state.wishlist.length === 0) {
        container.innerHTML = '<p class="empty-cart-msg">No items in wishlist</p>';
        return;
    }
    
    container.innerHTML = '';
    state.wishlist.forEach(item => {
        container.innerHTML += `
            <div class="cart-item fade-in" style="display:flex; justify-content:space-between; align-items:center;">
                <div class="cart-item-info">
                    <strong>${item.name}</strong>
                    <span>₹${item.price.toFixed(2)}</span>
                </div>
                <button class="btn btn-primary" style="padding:0.3rem;" onclick="addToCart(state.medicines.find(m=>m.id===${item.id}))">
                    <ion-icon name="cart-outline" style="margin:0;"></ion-icon>
                </button>
            </div>
        `;
    });
}
