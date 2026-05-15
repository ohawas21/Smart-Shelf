// ── WEBSOCKET ──────────────────────────────────────────────────────────────
const ws = new WebSocket(`ws://${window.location.host}/ws`);
const statusEl = document.getElementById('connection-status');
const alertBanner = document.getElementById('alert-banner');

ws.onopen = () => {
    statusEl.textContent = '● Connected';
    statusEl.className = 'status connected';
};

ws.onclose = () => {
    statusEl.textContent = '● Disconnected';
    statusEl.className = 'status';
    // Auto-reconnect after 3 seconds
};

ws.onerror = (err) => {
    console.error('WebSocket error:', err);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'ping') return;          // ignore heartbeat
    if (data.type === 'init') {
        initShelves(data.shelves);
    } else if (data.type === 'weight_update') {
        updateShelfUI(data);
        logEvent(data);
    } else if (data.type === 'threshold_update') {
        document.getElementById(`threshold-value-${data.shelf_id}`).textContent = data.threshold + 'g';
        document.getElementById(`threshold-display-${data.shelf_id}`).textContent = data.threshold + 'g threshold';
    }
};

// ── DRAG AND DROP ──────────────────────────────────────────────────────────
document.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('dragstart', e => {
        e.dataTransfer.setData('product_id', card.dataset.productId);
        card.classList.add('dragging');
    });
    card.addEventListener('dragend', () => card.classList.remove('dragging'));
});

async function handleDrop(event, shelfId) {
    event.preventDefault();
    document.getElementById(`drop-${shelfId}`).classList.remove('drag-over');

    const productId = event.dataTransfer.getData('product_id');
    if (!productId) return;

    const res = await fetch(`/api/shelf/${shelfId}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
    });

    if (res.ok) {
        const data = await res.json();
        renderShelfProducts(shelfId, data.shelf.products);
        updateWeightBar(shelfId, data.shelf.current_weight, data.shelf.threshold);
    }
}

async function removeProduct(shelfId, instanceId) {
    const res = await fetch(`/api/shelf/${shelfId}/remove/${instanceId}`, {
        method: 'DELETE'
    });

    if (res.ok) {
        const data = await res.json();
        renderShelfProducts(shelfId, data.shelf.products);
        updateWeightBar(shelfId, data.shelf.current_weight, data.shelf.threshold);

        if (data.event.alert) {
            showAlertBanner(data.shelf.name || shelfId);
        }
    }
}

async function updateThreshold(shelfId, value) {
    document.getElementById(`threshold-value-${shelfId}`).textContent = value + 'g';
    await fetch(`/api/shelf/${shelfId}/threshold`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold: parseInt(value) })
    });
}

// ── UI HELPERS ─────────────────────────────────────────────────────────────
function initShelves(shelves) {
    Object.entries(shelves).forEach(([id, shelf]) => {
        renderShelfProducts(id, shelf.products);
        updateWeightBar(id, shelf.current_weight, shelf.threshold);
    });
}

function renderShelfProducts(shelfId, products) {
    const container = document.getElementById(`products-${shelfId}`);
    if (products.length === 0) {
        container.innerHTML = '<span class="drop-hint">Drop products here</span>';
        return;
    }
    container.innerHTML = products.map(p => `
        <div class="shelf-product">
            <span>${p.emoji}</span>
            <span>${p.name}</span>
            <span style="color:#999;font-size:10px">${p.weight}g</span>
            <button class="remove-btn" onclick="removeProduct('${shelfId}', '${p.id}')">×</button>
        </div>
    `).join('');
}

function updateWeightBar(shelfId, weight, threshold) {
    const bar     = document.getElementById(`bar-${shelfId}`);
    const card    = document.getElementById(`shelf-${shelfId}`);
    const weightEl = document.getElementById(`weight-${shelfId}`);

    weightEl.textContent = weight + 'g';

    const pct = Math.min(100, (weight / (threshold * 2)) * 100);
    bar.style.width = pct + '%';

    bar.className  = 'weight-bar';
    card.className = 'shelf-card';

    if (weight === 0 || weight < threshold) {
        bar.classList.add('red');
        card.classList.add('critical');
    } else if (weight < threshold * 1.5) {
        bar.classList.add('amber');
        card.classList.add('warning');
    }
}

function updateShelfUI(data) {
    updateWeightBar(data.shelf_id, data.current_weight, data.threshold);
}

function showAlertBanner(shelfName) {
    alertBanner.textContent = `⚠️ ${shelfName} — Low stock alert sent!`;
    alertBanner.classList.remove('hidden');
    setTimeout(() => alertBanner.classList.add('hidden'), 5000);
}

function logEvent(data) {
    const log  = document.getElementById('event-log');
    const time = new Date().toLocaleTimeString();
    const isAlert = data.alert;

    const cls = isAlert ? 'alert' :
                data.action === 'add' ? 'success' : 'warning';

    const msg = isAlert
        ? `⚠️ ${data.shelf_name} — LOW STOCK ALERT (${data.current_weight}g < ${data.threshold}g)`
        : `${data.action === 'add' ? '➕' : '➖'} ${data.shelf_name}: ${data.product} ${data.action === 'add' ? 'added' : 'removed'} (${data.current_weight}g)`;

    const item = document.createElement('div');
    item.className = `event-item ${cls}`;
    item.textContent = `[${time}] ${msg}`;
    log.prepend(item);
}