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

document.addEventListener("DOMContentLoaded", function() {
    const track = document.getElementById('testimonialTrack');
    const dotsContainer = document.getElementById('sliderDots');

    if (!track || !dotsContainer) return;

    const cards = Array.from(track.children);
    let currentIndex = 0;
    let scrollInterval;

    // 1. Function to calculate how many dots we actually need
    function updateDots() {
        dotsContainer.innerHTML = ''; // Clear existing dots

        // How many cards are visible right now?
        const displayCount = window.innerWidth > 992 ? 3 : (window.innerWidth > 600 ? 2 : 1);

        // How many "steps" can the slider actually take?
        // If we have 4 cards and show 3, we only need 2 dots (Pos 0 and Pos 1)
        const maxDots = cards.length - displayCount + 1;

        if (maxDots <= 1) return; // Don't show dots if all cards fit on screen

        for (let i = 0; i < maxDots; i++) {
            const dot = document.createElement('div');
            dot.classList.add('dot');
            if (i === currentIndex) dot.classList.add('active');
            dot.addEventListener('click', () => goToSlide(i));
            dotsContainer.appendChild(dot);
        }
    }

    function goToSlide(index) {
        const displayCount = window.innerWidth > 992 ? 3 : (window.innerWidth > 600 ? 2 : 1);
        const maxIndex = cards.length - displayCount;

        // Loop back to start if at the end
        if (index > maxIndex) {
            currentIndex = 0;
        } else if (index < 0) {
            currentIndex = maxIndex;
        } else {
            currentIndex = index;
        }

        const cardWidth = cards[0].offsetWidth;
        const gap = 28; // matching the 1.75rem gap in CSS
        const amountToMove = (cardWidth + gap) * currentIndex;

        track.style.transform = `translateX(-${amountToMove}px)`;

        // Update dot highlight
        const dots = document.querySelectorAll('.dot');
        dots.forEach((d, i) => d.classList.toggle('active', i === currentIndex));
    }

    // 2. Autoplay Timer
    function startAutoplay() {
        scrollInterval = setInterval(() => {
            const displayCount = window.innerWidth > 992 ? 3 : (window.innerWidth > 600 ? 2 : 1);
            if (currentIndex >= cards.length - displayCount) {
                goToSlide(0);
            } else {
                goToSlide(currentIndex + 1);
            }
        }, 5000);
    }

    // 3. Pause on Hover
    track.parentElement.addEventListener('mouseenter', () => clearInterval(scrollInterval));
    track.parentElement.addEventListener('mouseleave', () => startAutoplay());

    // 4. Initialization & Window Resize
    updateDots();
    startAutoplay();

    window.addEventListener('resize', () => {
        updateDots();
        goToSlide(currentIndex); // Recalculate position for new screen size
    });
});