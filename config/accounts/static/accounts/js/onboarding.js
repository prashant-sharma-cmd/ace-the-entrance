/* ============================================================
   onboarding.js — multi-step wizard logic
   ============================================================ */

'use strict';

(function () {
  const TOTAL = 4;
  let current = 1;

  const stepLabels = ['Purpose', 'Frequency', 'Discovery', 'Finish'];

  /* ── DOM refs ─────────────────────────────────────────── */
  function panel(n)  { return document.getElementById(`ob-panel-${n}`); }
  function dot(n)    { return document.getElementById(`ob-dot-${n}`); }
  function dotLine(n){ return document.getElementById(`ob-line-${n}`); }
  function label(n)  { return document.getElementById(`ob-label-${n}`); }

  const progressText = document.getElementById('ob-progress-text');
  const summaryPurpose = document.getElementById('sum-purpose');
  const summaryFreq    = document.getElementById('sum-freq');
  const summaryDisc    = document.getElementById('sum-disc');

  /* ── Navigation ───────────────────────────────────────── */
function goTo(n) {
  // Hide current panel
  panel(current)?.classList.remove('active');

  // Mark dots as done/inactive
  if (n > current) {
    dot(current)?.classList.remove('active');
    dot(current)?.classList.add('done');
    // Fill the line between current and next
    dotLine(current)?.style.setProperty('background', 'var(--clr-primary)');
  }

  if (n < current) {
    // Going back — remove done from current
    dot(current)?.classList.remove('active', 'done');
    dotLine(n)?.style.setProperty('background', '#dde4f5');
  }

  current = n;

  // Activate new panel and dot
  panel(current)?.classList.add('active');
  dot(current)?.classList.remove('done');
  dot(current)?.classList.add('active');

  // Update all labels
  for (let i = 1; i <= TOTAL; i++) {
    label(i)?.classList.toggle('active', i === current);
  }

  if (progressText) progressText.textContent = `Step ${current} of ${TOTAL}`;
  if (current === TOTAL) fillSummary();

  document.querySelector('.auth-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

    current = n;
    panel(current)?.classList.add('active');
    dot(current)?.classList.add('active');
    label(current)?.classList.add('active');

    // Update sibling labels
    for (let i = 1; i <= TOTAL; i++) {
      label(i)?.classList.toggle('active', i === current);
    }

    // Update progress text
    if (progressText) progressText.textContent = `Step ${current} of ${TOTAL}`;

    // Fill summary on last step
    if (current === TOTAL) fillSummary();

    // Scroll card into view smoothly
    document.querySelector('.auth-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ── Summary fill ─────────────────────────────────────── */
  function getCheckedLabel(name) {
    const el = document.querySelector(`input[name="${name}"]:checked`);
    if (!el) return '—';
    const lbl = document.querySelector(`label[for="${el.id}"]`);
    return lbl ? lbl.querySelector('.ob-choice-text')?.textContent.trim() || '—' : el.value;
  }

  function fillSummary() {
    if (summaryPurpose) summaryPurpose.textContent = getCheckedLabel('primary_purpose');
    if (summaryFreq)    summaryFreq.textContent    = getCheckedLabel('visit_frequency');
    if (summaryDisc)    summaryDisc.textContent    = getCheckedLabel('how_discovered');
  }

  /* ── Expose to inline onclick handlers ───────────────── */
  window.obGoTo = goTo;

  /* ── Form submit loading state ─────────────────────────  */
  document.addEventListener('DOMContentLoaded', () => {
    // Init first panel
    panel(1)?.classList.add('active');
    dot(1)?.classList.add('active');
    label(1)?.classList.add('active');

    const form = document.getElementById('ob-form');
    const btn  = document.getElementById('ob-submit');
    if (form && btn) {
      form.addEventListener('submit', () => {
        btn.disabled      = true;
        btn.style.opacity = '0.7';
        btn.innerHTML     = '<i class="fas fa-spinner fa-spin"></i>&nbsp; Saving…';
      });
    }
  });
})();