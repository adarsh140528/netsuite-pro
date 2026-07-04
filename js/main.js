/**
 * NetSuite Pro - Main JavaScript
 * Shared utilities, theme management, navigation
 */

// ── Theme Management ──────────────────────────────────────
const ThemeManager = {
  init() {
    const saved = localStorage.getItem('netsuite-theme') || 'light';
    this.apply(saved);
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    this.apply(next);
  },
  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('netsuite-theme', theme);
    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.querySelector('.theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
      btn.querySelector('.theme-label').textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
  }
};

// ── Sidebar / Navigation ─────────────────────────────────
const Nav = {
  init() {
    // Highlight active nav item
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(el => {
      const href = el.getAttribute('href');
      if (href === path || (path === '/' && href === '/')) {
        el.classList.add('active');
      }
    });

    // Mobile hamburger
    const ham = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    if (ham && sidebar) {
      ham.addEventListener('click', () => sidebar.classList.toggle('open'));
      document.addEventListener('click', e => {
        if (!sidebar.contains(e.target) && !ham.contains(e.target)) {
          sidebar.classList.remove('open');
        }
      });
    }
  }
};

// ── API Helper ───────────────────────────────────────────
async function apiPost(endpoint, payload) {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

// ── UI Helpers ───────────────────────────────────────────
function showAlert(containerId, msg, type = 'error') {
  const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="alert alert-${type}">
      <span>${icons[type]}</span>
      <span>${msg}</span>
    </div>`;
  el.classList.remove('hidden');
}

function clearAlert(containerId) {
  const el = document.getElementById(containerId);
  if (el) { el.innerHTML = ''; el.classList.add('hidden'); }
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (loading) {
    btn._originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Processing...';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._originalText || 'Calculate';
    btn.disabled = false;
  }
}

function showSection(id) {
  document.querySelectorAll('.result-section').forEach(el => el.classList.add('hidden'));
  const el = document.getElementById(id);
  if (el) { el.classList.remove('hidden'); el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
}

// ── Binary Renderer ──────────────────────────────────────
function renderBinaryBits(flatBin, cidr, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  let html = '<div class="binary-display">';
  let pos = 0;
  flatBin.split('').forEach((bit, i) => {
    if (i > 0 && i % 8 === 0) {
      html += '<span class="bit-separator">.</span>';
    }
    const cls = i < cidr ? 'bit-network' : 'bit-host';
    html += `<span class="bit ${cls}" title="bit ${i+1}">${bit}</span>`;
    pos++;
  });
  html += '</div>';
  container.innerHTML = html;
}

// ── Export Helper ────────────────────────────────────────
async function exportData(data, format, title) {
  const res = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data, format, title })
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Number Formatter ─────────────────────────────────────
function fmt(n) {
  return Number(n).toLocaleString();
}

// ── Init on DOM ready ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  Nav.init();

  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) themeBtn.addEventListener('click', () => ThemeManager.toggle());
});
