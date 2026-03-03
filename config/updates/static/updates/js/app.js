  function switchTab(tab, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    btn.classList.add('active');
    // re-trigger reveal for newly visible cards
    triggerReveal();
  }

  function triggerReveal() {
    const els = document.querySelectorAll('.reveal:not(.visible)');
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
    els.forEach(el => obs.observe(el));
  }

  // Initial reveal on load
  document.addEventListener('DOMContentLoaded', triggerReveal);