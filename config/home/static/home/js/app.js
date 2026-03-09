// Navbar
const hamburger = document.getElementById('nav-hamburger');
const navbar = document.getElementById('navbar');
if (hamburger && navbar) {
  hamburger.addEventListener('click', () => navbar.classList.toggle('nav-open'));

  navbar.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => navbar.classList.remove('nav-open'));
  });
}
//setup date
const date = (document.getElementById(
  "date"
).innerHTML = new Date().getFullYear());

window.MathJax = {
tex: { inlineMath: [['$', '$'], ['\\(', '\\)']] }
};

document.querySelectorAll('.toast-msg').forEach(el => {
  el.addEventListener('animationend', (e) => {
    if (e.animationName === 'toastOut') el.remove();
  });
});