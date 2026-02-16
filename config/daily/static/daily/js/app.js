/**
 * Quiz Application — app.js
 *
 * Visibility is controlled exclusively via el.style.display.
 * Inline styles always beat stylesheet rules — no specificity conflicts.
 *
 * Flow:
 *  1. DOMContentLoaded  → hide quiz/results/loading via JS; show splash
 *  2. loadQuestions()   → fetches silently in the background
 *  3. Questions ready   → enable Start button, fill question count
 *  4. startQuiz()       → hide splash, show quiz card
 *  5. submitQuiz()      → hide quiz, show results
 *  6. restartQuiz()     → hide results, show splash
 */

let questions            = [];
let currentQuestionIndex = 0;
let userAnswers          = [];
let score                = 0;
let questionsReady       = false;

/* ── Inline display helpers — always override CSS ── */
function showEl(id, displayValue) {
    const el = document.getElementById(id);
    if (el) el.style.display = displayValue || 'block';
}
function hideEl(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

/* ════════════════════════════════════════
   INIT — set initial state immediately
════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
    /* Force-hide everything except splash via inline style */
    hideEl('loading');
    hideEl('quiz-content');
    hideEl('results');

    /* Splash is already visible in HTML — no need to show it */
    loadQuestions();
});

/* ════════════════════════════════════════
   FETCH QUESTIONS
════════════════════════════════════════ */
async function loadQuestions() {
    try {
        const response = await fetch(window.QUIZ_API_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data   = await response.json();
        questions    = data.questions;
        userAnswers  = new Array(questions.length).fill(null);
        questionsReady = true;

        /* Update splash stats */
        const splashTotal = document.getElementById('splash-total');
        if (splashTotal) splashTotal.textContent = questions.length;

        /* Hide fetch dots, unlock Start button */
        hideEl('fetch-indicator');
        const startBtn = document.getElementById('start-btn');
        if (startBtn) startBtn.disabled = false;

    } catch (err) {
        console.error('Error loading questions:', err);
        const ind = document.getElementById('fetch-indicator');
        if (ind) {
            ind.innerHTML =
                '<span style="color:#b91c1c;font-size:.85rem">&#9888; Failed to load. Please refresh.</span>';
        }
    }
}

/* ════════════════════════════════════════
   SPLASH → QUIZ
════════════════════════════════════════ */
function startQuiz() {
    if (!questionsReady) return;

    const splash = document.getElementById('splash');

    /* Animate splash out */
    splash.style.transition = 'opacity .28s ease, transform .28s ease';
    splash.style.opacity    = '0';
    splash.style.transform  = 'translateY(-14px) scale(.98)';

    setTimeout(() => {
        hideEl('splash');
        splash.style.transition = '';
        splash.style.opacity    = '';
        splash.style.transform  = '';

        document.getElementById('total-questions').textContent = questions.length;

        /* Show quiz card */
        showEl('quiz-content', 'block');
        displayQuestion();
    }, 280);
}

/* ════════════════════════════════════════
   QUIZ DISPLAY
════════════════════════════════════════ */

/**
 * Safely format text: escape HTML first, then apply chemistry formatting.
 * Order matters — escape before injecting <sub> tags.
 */
function safeFormat(str) {
    /* 1. Pull out $…$ content first (raw, before escaping) */
    const stripped = str.replace(/\$([^$]+)\$/g, (_, inner) => inner);
    /* 2. Escape any remaining HTML special chars */
    const escaped  = escapeHtml(stripped);
    /* 3. Now safely convert _2 or _{2} → <sub>2</sub> */
    return escaped.replace(/_\{?(\w+)\}?/g, '<sub>$1</sub>');
}

function displayQuestion() {
    const question  = questions[currentQuestionIndex];
    const container = document.getElementById('question-container');

    let html = `<div class="question-text fade-in">${safeFormat(question.question)}</div>
                <div class="choices">`;

    question.choices.forEach((choice) => {
        const isSelected    = userAnswers[currentQuestionIndex] === choice.id;
        const selectedClass = isSelected ? 'selected' : '';

        html += `
            <button class="choice-btn ${selectedClass}"
                    onclick="selectAnswer(${choice.id})"
                    data-choice-id="${choice.id}">
                ${safeFormat(choice.text)}
            </button>`;
    });

    html += '</div>';
    container.innerHTML = html;

    updateNavigation();
    updateProgress();
    updateQuestionCounter();
}

function selectAnswer(choiceId) {
    userAnswers[currentQuestionIndex] = choiceId;
    displayQuestion();
}

function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        displayQuestion();
    }
}

function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion();
    }
}

function updateNavigation() {
    const prevBtn   = document.getElementById('prev-btn');
    const nextBtn   = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');

    prevBtn.disabled = currentQuestionIndex === 0;

    const isLast = currentQuestionIndex === questions.length - 1;
    nextBtn.style.display   = isLast ? 'none'         : 'inline-block';
    submitBtn.style.display = isLast ? 'inline-block' : 'none';
}

function updateProgress() {
    const answered = userAnswers.filter(a => a !== null).length;
    document.getElementById('progress-fill').style.width =
        ((answered / questions.length) * 100) + '%';
    document.getElementById('total-answered').textContent = answered;
}

function updateQuestionCounter() {
    document.getElementById('current-question').textContent = currentQuestionIndex + 1;
}

/* ════════════════════════════════════════
   SUBMIT & RESULTS
════════════════════════════════════════ */
function submitQuiz() {
    const unanswered = userAnswers.filter(a => a === null).length;
    if (unanswered > 0) {
        if (!confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) return;
    }

    score = 0;
    questions.forEach((q, i) => {
        const correct = q.choices.find(c => c.isCorrect);
        if (userAnswers[i] === correct.id) score++;
    });

    showResults();
}

function showResults() {
    hideEl('quiz-content');
    showEl('results', 'block');

    const pct = Math.round((score / questions.length) * 100);
    document.getElementById('final-score').textContent = score;
    document.getElementById('final-total').textContent = questions.length;
    document.getElementById('percentage').textContent  = pct;

    document.getElementById('performance-message-container').innerHTML =
        `<p class="performance-msg">${getPerformanceMessage(pct)}</p>`;
}

function getPerformanceMessage(pct) {
    if (pct === 100) return '🎉 Perfect score! Excellent work!';
    if (pct >= 80)   return '👏 Great job! You did really well!';
    if (pct >= 60)   return '👍 Good effort! Keep it up!';
    if (pct >= 40)   return "💪 Not bad, but there's room for improvement!";
    return '📚 Keep studying and try again!';
}

/* ════════════════════════════════════════
   RESTART → back to splash
════════════════════════════════════════ */
function restartQuiz() {
    currentQuestionIndex = 0;
    userAnswers          = new Array(questions.length).fill(null);
    score                = 0;

    hideEl('results');
    showEl('splash', 'block');
}

/* ════════════════════════════════════════
   UTILS
════════════════════════════════════════ */
function escapeHtml(text) {
    const map = { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/* ════════════════════════════════════════
   KEYBOARD NAV
════════════════════════════════════════ */
document.addEventListener('keydown', (e) => {
    const qc = document.getElementById('quiz-content');
    if (!qc || qc.style.display === 'none' || qc.style.display === '') return;

    if (e.key === 'ArrowLeft'  && currentQuestionIndex > 0)                    previousQuestion();
    if (e.key === 'ArrowRight' && currentQuestionIndex < questions.length - 1) nextQuestion();

    if (e.key >= '1' && e.key <= '4') {
        const idx = parseInt(e.key) - 1;
        const q   = questions[currentQuestionIndex];
        if (q && q.choices[idx]) selectAnswer(q.choices[idx].id);
    }
});

/* ── Global exposure for inline onclick ── */
window.startQuiz        = startQuiz;
window.selectAnswer     = selectAnswer;
window.nextQuestion     = nextQuestion;
window.previousQuestion = previousQuestion;
window.submitQuiz       = submitQuiz;
window.restartQuiz      = restartQuiz;