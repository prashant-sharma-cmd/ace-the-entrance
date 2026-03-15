 /* ── Lightbox ── */
  function openLightbox(src, caption) {
    const overlay = document.getElementById('lightbox');
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox-img').alt = caption;
    document.getElementById('lightbox-caption').textContent = caption;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
    document.body.style.overflow = '';
  }

  function closeLightboxOnOverlay(e) {
    // Close only when clicking the dark backdrop, not the image itself
    if (e.target === document.getElementById('lightbox')) closeLightbox();
  }

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });

  /* ── Tab switching ── */
  function switchTab(tab, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    btn.classList.add('active');
    triggerReveal();
  }

  /* ── Scroll reveal ── */
  function triggerReveal() {
    const els = document.querySelectorAll('.reveal:not(.visible)');
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
    els.forEach(el => obs.observe(el));
  }

  document.addEventListener('DOMContentLoaded', triggerReveal);