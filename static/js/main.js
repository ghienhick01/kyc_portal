/* ─── VerifyID KYC Portal — Main JavaScript ─────────────────────────────── */

'use strict';

// ─── Auto-dismiss alerts ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-4px)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
});

// ─── Sidebar toggle (mobile) ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth > 900) return;
    if (!sidebar.contains(e.target) && !e.target.closest('.topbar-toggle')) {
      sidebar.classList.remove('open');
    }
  });
});

// ─── File drag & drop ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('file-drop');
  if (!dropZone) return;

  const fileInput = dropZone.querySelector('input[type="file"]');
  const display = document.getElementById('file-name-display');

  ['dragover', 'dragenter'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--accent)';
      dropZone.style.background = 'var(--accent-glow)';
    });
  });

  ['dragleave', 'dragend'].forEach(evt => {
    dropZone.addEventListener(evt, () => {
      dropZone.style.borderColor = '';
      dropZone.style.background = '';
    });
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    dropZone.style.background = '';
    const files = e.dataTransfer.files;
    if (files.length > 0 && fileInput) {
      fileInput.files = files;
      if (display) {
        display.textContent = files[0].name;
        display.style.color = 'var(--accent)';
      }
    }
  });
});

// ─── Confirm dialogs (data-confirm attribute) ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });
});

// ─── Progress bar animation ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const bar = document.querySelector('.progress-bar-fill');
  if (bar) {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = targetWidth; }, 100);
    });
  }
});

// ─── Table row click to navigate ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.table-row[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => {
      window.location.href = row.dataset.href;
    });
  });
});

// ─── Password toggle ─────────────────────────────────────────────────────────
function togglePassword(btn) {
  const wrap = btn.closest('.input-password-wrap');
  if (!wrap) return;
  const input = wrap.querySelector('input');
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
  const icon = btn.querySelector('.eye-icon');
  if (icon) icon.style.opacity = input.type === 'text' ? '0.5' : '1';
}

// ─── File name display ────────────────────────────────────────────────────────
function updateFileName(input) {
  const display = document.getElementById('file-name-display');
  if (!display) return;
  if (input.files && input.files[0]) {
    display.textContent = input.files[0].name;
    display.style.color = 'var(--accent)';
  }
}

// ─── Show rejection field ─────────────────────────────────────────────────────
function showRejectionField() {
  const group = document.getElementById('rejection-reason-group');
  if (group) group.style.display = 'block';
}

// ─── Copy to clipboard ───────────────────────────────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    btn.style.color = 'var(--green)';
    setTimeout(() => {
      btn.textContent = original;
      btn.style.color = '';
    }, 1500);
  });
}

// ─── Stats counter animation ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const statValues = document.querySelectorAll('.stat-value');
  statValues.forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 20));
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 40);
  });
});

// ─── Filter form: enter key submit ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const filterInputs = document.querySelectorAll('.filter-input');
  filterInputs.forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        input.closest('form')?.submit();
      }
    });
  });
});
