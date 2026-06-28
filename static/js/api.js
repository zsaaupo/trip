/* ------------------------------------------------------------------ *
 * Make a trip - shared front-end helpers
 * Every page includes this file. It wraps fetch() so every call to the
 * Django REST API automatically sends the session cookie + CSRF token,
 * and provides small UI helpers (toasts, formatting) used everywhere.
 * ------------------------------------------------------------------ */

const API_BASE = '/api';

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? decodeURIComponent(match.pop()) : '';
}

/**
 * apiRequest('/hotels/', { method: 'POST', body: {...} })
 * - body may be a plain object (sent as JSON) or a FormData instance
 *   (sent as-is, for image uploads).
 */
async function apiRequest(path, options = {}) {
  const { method = 'GET', body = null } = options;
  const isForm = body instanceof FormData;
  const headers = {};
  if (!isForm && body !== null) headers['Content-Type'] = 'application/json';
  if (method !== 'GET') headers['X-CSRFToken'] = getCookie('csrftoken');

  const fetchOptions = { method, headers, credentials: 'same-origin' };
  if (body !== null) fetchOptions.body = isForm ? body : JSON.stringify(body);

  const res = await fetch(API_BASE + path, fetchOptions);

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch (e) { data = text; }
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.message)) ||
      (data && typeof data === 'object' ? firstErrorMessage(data) : null) ||
      'Something went wrong. Please try again.';
    const err = new Error(message);
    err.data = data;
    err.status = res.status;
    throw err;
  }
  return data;
}

function firstErrorMessage(data) {
  for (const key in data) {
    const val = data[key];
    if (Array.isArray(val) && val.length) return val[0];
    if (typeof val === 'string') return val;
  }
  return null;
}

/* ----------------------------- Toasts ----------------------------- */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) { alert(message); return; }
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

/* --------------------------- Formatting ---------------------------- */
function formatMoney(value) {
  const n = Number(value || 0);
  return 'Tk ' + n.toFixed(2);
}

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function statusBadgeClass(status) {
  return {
    pending: 'badge badge--pending',
    confirmed: 'badge badge--confirmed',
    declined: 'badge badge--declined',
    cancelled: 'badge badge--cancelled',
    completed: 'badge badge--completed',
    approved: 'badge badge--confirmed',
  }[status] || 'badge';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

/* ------------------------- Global UI wiring ------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  const navToggle = document.getElementById('nav-toggle');
  const mainNav = document.getElementById('main-nav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', () => mainNav.classList.toggle('main-nav--open'));
  }

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/accounts/logout/', { method: 'POST', body: {} });
      } catch (e) { /* ignore */ }
      window.location.href = '/';
    });
  }
});
