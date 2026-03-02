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

document.addEventListener("DOMContentLoaded", function() {
  const authors = document.querySelectorAll('.author-slider-wrapper .author-inner');
  let current = 0;

  if (authors.length > 1) {
    setInterval(() => {
      // Hide current
      authors[current].classList.remove('active');

      // Move to next
      current = (current + 1) % authors.length;

      // Show next
      authors[current].classList.add('active');
    }, 4000); // Switches every 4 seconds
  }
});