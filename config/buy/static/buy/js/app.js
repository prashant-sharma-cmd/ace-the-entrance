  /* ── Map focus ── */
  function focusShop(el, lat, lng, name) {
    document.querySelectorAll('.shop-item').forEach(s => s.classList.remove('active'));
    el.classList.add('active');
    const iframe = document.getElementById('shop-map');
    iframe.src = `https://maps.google.com/maps?q=${lat},${lng}&z=16&output=embed`;
  }

  /* ── Smooth scroll with offset ── */
  function smoothScroll(id) {
    event.preventDefault();
    const el = document.getElementById(id);
    if (!el) return;
    const offset = 72;
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  }

  /* ── Scroll reveal ── */
  const revealEls = document.querySelectorAll('.reveal');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.1 });
  revealEls.forEach(el => obs.observe(el));

  /* ── Auto-scroll to form if messages present (after redirect) ── */
  {% if messages %}
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      const el = document.getElementById('order-delivery');
      if (el) {
        const top = el.getBoundingClientRect().top + window.scrollY - 72;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    }, 200);
  });
  {% endif %}

  /* ── Auto-scroll to delivery section if form was submitted ── */
  {% if active_section == 'delivery' %}
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => smoothScroll('order-delivery'), 300);
  });
  {% endif %}