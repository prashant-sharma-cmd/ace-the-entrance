/* ── Map: highlight shop card and re-focus iframe ── */
function focusShop(el, embedUrl) {
  document.querySelectorAll('.shop-item').forEach(function (s) {
    s.classList.remove('active');
  });
  el.classList.add('active');
  var iframe = document.getElementById('shop-map');
  if (iframe) iframe.src = embedUrl;
}

/* ── Smooth scroll to a section by id, with navbar offset ── */
function smoothScroll(id, e) {
  if (e) e.preventDefault();
  var el = document.getElementById(id);
  if (!el) return;
  var offset = 72;
  var top = el.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top: top, behavior: 'smooth' });
}

/* ── Scroll reveal ── */
function initReveal() {
  var revealEls = document.querySelectorAll('.reveal');

  /* Graceful fallback for browsers without IntersectionObserver */
  if (!('IntersectionObserver' in window)) {
    revealEls.forEach(function (el) { el.classList.add('visible'); });
    return;
  }

  var obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, {
    threshold: 0,
    rootMargin: '0px 0px -40px 0px'
  });

  revealEls.forEach(function (el) { obs.observe(el); });

  /* Hard fallback: force-reveal anything still hidden after 1.5s */
  setTimeout(function () {
    document.querySelectorAll('.reveal:not(.visible)').forEach(function (el) {
      el.classList.add('visible');
    });
  }, 1500);
}

/* Run as soon as DOM is ready */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReveal);
} else {
  initReveal();
}