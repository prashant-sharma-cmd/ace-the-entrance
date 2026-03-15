/* ============================================================
   auth.js — shared utilities for all auth pages
   ============================================================ */

'use strict';

/* ── Password visibility toggle ──────────────────────── */
function initPasswordToggles() {
  document.querySelectorAll('[data-pw-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.pwToggle);
      if (!target) return;
      const isPassword = target.type === 'password';
      target.type = isPassword ? 'text' : 'password';
      const icon = btn.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-eye',      !isPassword);
        icon.classList.toggle('fa-eye-slash', isPassword);
      }
    });
  });
}

/* ── Password strength meter ──────────────────────────── */
function initStrengthMeter(inputId, barId, labelId) {
  const input = document.getElementById(inputId);
  const bar   = document.getElementById(barId);
  const label = document.getElementById(labelId);
  if (!input || !bar || !label) return;

  const levels = [
    { pct: '0%',    bg: '#e4eaf5', text: '',              color: '#aab4cc' },
    { pct: '25%',   bg: '#ef4444', text: 'Weak',          color: '#ef4444' },
    { pct: '50%',   bg: '#f59e0b', text: 'Fair',          color: '#f59e0b' },
    { pct: '75%',   bg: '#3b82f6', text: 'Good',          color: '#3b82f6' },
    { pct: '100%',  bg: '#22c55e', text: 'Strong ✓',      color: '#22c55e' },
  ];

  input.addEventListener('input', () => {
    const v = input.value;
    let score = 0;
    if (v.length >= 8)             score++;
    if (/[A-Z]/.test(v))           score++;
    if (/[0-9]/.test(v))           score++;
    if (/[^A-Za-z0-9]/.test(v))    score++;
    const lvl = v.length === 0 ? 0 : score;
    bar.style.width      = levels[lvl].pct;
    bar.style.background = levels[lvl].bg;
    label.textContent    = levels[lvl].text;
    label.style.color    = levels[lvl].color;
  });
}

/* ── Password match validation ────────────────────────── */
function initPasswordMatch(pw1Id, pw2Id, errorId, submitId) {
  const pw1    = document.getElementById(pw1Id);
  const pw2    = document.getElementById(pw2Id);
  const err    = document.getElementById(errorId);
  const submit = document.getElementById(submitId);
  if (!pw1 || !pw2) return;

  function check() {
    const mismatch = pw2.value && pw1.value !== pw2.value;
    if (err) err.style.display = mismatch ? 'flex' : 'none';
    if (submit) {
      submit.disabled      = mismatch;
      submit.style.opacity = mismatch ? '0.55' : '1';
    }
    pw2.classList.toggle('is-error', mismatch);
  }
  pw1.addEventListener('input', check);
  pw2.addEventListener('input', check);
}

/* ── Loading state on form submit ─────────────────────── */
function initLoadingSubmit(formId, btnId, loadingText = 'Please wait…') {
  const form = document.getElementById(formId);
  const btn  = document.getElementById(btnId);
  if (!form || !btn) return;
  form.addEventListener('submit', () => {
    btn.disabled     = true;
    btn.style.opacity = '0.7';
    btn.innerHTML    = `<i class="fas fa-spinner fa-spin"></i>&nbsp; ${loadingText}`;
  });
}

/* ── Init all shared behaviours ───────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();
});