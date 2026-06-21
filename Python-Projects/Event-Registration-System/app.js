/* ============================================================
   app.js — Event Registration System frontend logic
   
   All API calls use the BASE path so the app works correctly
   through the Replit reverse proxy at /events-api/.
   ============================================================ */

// The proxy mounts Flask at /events-api, so all API calls
// must start with this prefix.
const BASE = '/events-api';

// ── Utility: format ISO date string into readable text ───────
function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    weekday: 'short', year: 'numeric',
    month: 'long', day: 'numeric'
  }) + '  ·  ' + d.toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit'
  });
}

// ── Utility: get initials from a full name ───────────────────
function initials(name) {
  return name.trim().split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

// ── Toast notification system ────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Generic fetch wrapper with error handling ─────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

// ── Event card builder ───────────────────────────────────────
function buildEventCard(event) {
  const card = document.createElement('div');
  card.className = 'event-card';
  card.dataset.id = event.id;

  const desc = event.description
    ? `<p class="card-description">${event.description}</p>`
    : `<p class="card-description" style="color:var(--gray-400);font-style:italic;">No description provided.</p>`;

  card.innerHTML = `
    <div class="card-accent"></div>
    <div class="card-body">
      <h3 class="card-title">${event.name}</h3>
      <div class="card-date">📅 ${formatDate(event.date)}</div>
      ${desc}
      <div class="card-meta">
        👥 <span class="badge">${event.registration_count}</span>
        registered
      </div>
    </div>
    <div class="card-footer">
      <button class="btn btn-primary btn-sm" onclick="openRegisterModal(${event.id}, '${event.name.replace(/'/g, "\\'")}')">
        ✏️ Register
      </button>
      <button class="btn btn-outline btn-sm" onclick="openViewModal(${event.id}, '${event.name.replace(/'/g, "\\'")}')">
        👥 Attendees
      </button>
    </div>
  `;
  return card;
}

// ── Load and render all events ───────────────────────────────
async function loadEvents() {
  const grid = document.getElementById('eventsGrid');
  grid.innerHTML = `<p style="color:var(--gray-400);grid-column:1/-1;text-align:center;padding:2rem;">
    <span class="spinner" style="border-color:rgba(0,0,0,.15);border-top-color:var(--primary);"></span>
    Loading events…
  </p>`;

  try {
    const { events } = await apiFetch('/events');
    grid.innerHTML = '';

    if (!events.length) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <div class="empty-icon">📋</div>
          <div class="empty-title">No events yet</div>
          <div class="empty-sub">Create your first event to get started.</div>
          <button class="btn btn-primary" onclick="openCreateModal()">+ Create Event</button>
        </div>`;
      return;
    }

    events.forEach(e => grid.appendChild(buildEventCard(e)));
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--danger);grid-column:1/-1;padding:2rem;">
      Failed to load events: ${err.message}
    </p>`;
  }
}

// ── Create Event modal ───────────────────────────────────────
function openCreateModal() {
  document.getElementById('createForm').reset();
  document.getElementById('createError').textContent = '';
  document.getElementById('createOverlay').classList.add('open');
}

function closeCreateModal() {
  document.getElementById('createOverlay').classList.remove('open');
}

async function submitCreateEvent(e) {
  e.preventDefault();
  const errorEl = document.getElementById('createError');
  const btn = document.getElementById('createSubmitBtn');
  errorEl.textContent = '';

  const name = document.getElementById('eventName').value.trim();
  const date = document.getElementById('eventDate').value;
  const description = document.getElementById('eventDesc').value.trim();

  if (!name || !date) {
    errorEl.textContent = 'Name and date are required.';
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Creating…';

  try {
    await apiFetch('/events', {
      method: 'POST',
      body: JSON.stringify({ name, date, description: description || undefined }),
    });
    closeCreateModal();
    showToast('Event created successfully!', 'success');
    loadEvents();
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Create Event';
  }
}

// ── Register for Event modal ─────────────────────────────────
let activeEventId = null;

function openRegisterModal(id, name) {
  activeEventId = id;
  document.getElementById('registerEventName').textContent = name;
  document.getElementById('registerForm').reset();
  document.getElementById('registerError').textContent = '';
  document.getElementById('registerOverlay').classList.add('open');
}

function closeRegisterModal() {
  document.getElementById('registerOverlay').classList.remove('open');
  activeEventId = null;
}

async function submitRegister(e) {
  e.preventDefault();
  const errorEl = document.getElementById('registerError');
  const btn = document.getElementById('registerSubmitBtn');
  errorEl.textContent = '';

  const user_name = document.getElementById('userName').value.trim();
  const user_email = document.getElementById('userEmail').value.trim();

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Registering…';

  try {
    await apiFetch(`/events/${activeEventId}/register`, {
      method: 'POST',
      body: JSON.stringify({ user_name, user_email }),
    });
    closeRegisterModal();
    showToast(`Registered for the event!`, 'success');
    loadEvents(); // refresh registration counts
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Register';
  }
}

// ── View Attendees modal ─────────────────────────────────────
async function openViewModal(id, name) {
  document.getElementById('viewEventName').textContent = name;
  document.getElementById('viewList').innerHTML = `
    <li style="padding:.75rem 0;color:var(--gray-400);">
      <span class="spinner" style="border-color:rgba(0,0,0,.1);border-top-color:var(--primary);"></span>
      Loading…
    </li>`;
  document.getElementById('viewOverlay').classList.add('open');

  try {
    const { registrations, total } = await apiFetch(`/events/${id}/registrations`);
    document.getElementById('viewTotal').textContent = `${total} registered`;
    const list = document.getElementById('viewList');

    if (!registrations.length) {
      list.innerHTML = `<li style="padding:1rem 0;color:var(--gray-400);text-align:center;">
        No one has registered yet.</li>`;
      return;
    }

    list.innerHTML = registrations.map(r => `
      <li class="reg-item">
        <div class="reg-avatar">${initials(r.user_name)}</div>
        <div>
          <div class="reg-name">${r.user_name}</div>
          <div class="reg-email">${r.user_email}</div>
        </div>
      </li>`).join('');
  } catch (err) {
    document.getElementById('viewList').innerHTML = `
      <li style="color:var(--danger);padding:.75rem 0;">Failed: ${err.message}</li>`;
  }
}

function closeViewModal() {
  document.getElementById('viewOverlay').classList.remove('open');
}

// ── Close modal on backdrop click ────────────────────────────
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});

// ── Boot ─────────────────────────────────────────────────────
loadEvents();
