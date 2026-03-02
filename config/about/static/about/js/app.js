// Scroll reveal
const revealEls = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
entries.forEach(e => {
  if (e.isIntersecting) {
    e.target.classList.add('visible');
    observer.unobserve(e.target);
  }
});
}, { threshold: 0.12 });
revealEls.forEach(el => observer.observe(el));