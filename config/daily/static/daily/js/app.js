/**
 * Quiz Application - Main JavaScript
 */

// Global variables
let questions = [];
let currentQuestionIndex = 0;
let userAnswers = [];
let score = 0;


async function loadQuestions() {
    try {
        const response = await fetch(window.QUIZ_API_URL);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        questions = data.questions;

        // Initialize user answers array
        userAnswers = new Array(questions.length).fill(null);

        // Hide loading, show quiz
        document.getElementById('loading').style.display = 'none';
        document.getElementById('quiz-content').style.display = 'block';
        document.getElementById('total-questions').textContent = questions.length;

        // Display first question
        displayQuestion();
    } catch (error) {
        console.error('Error loading questions:', error);
        showError('Error loading quiz. Please refresh the page.');
    }
}

/**
 * Display current question
 */
function displayQuestion() {
    const question = questions[currentQuestionIndex];
    const container = document.getElementById('question-container');

    let html = `
        <div class="question-text">${escapeHtml(question.question)}</div>
        <div class="choices">
    `;

    question.choices.forEach((choice, index) => {
        const isSelected = userAnswers[currentQuestionIndex] === choice.id;
        const selectedClass = isSelected ? 'selected' : '';

        html += `
            <button class="choice-btn ${selectedClass}"
                    onclick="selectAnswer(${choice.id})"
                    data-choice-id="${choice.id}">
                ${escapeHtml(choice.text)}
            </button>
        `;
    });

    html += '</div>';
    container.innerHTML = html;

    updateNavigation();
    updateProgress();
    updateQuestionCounter();
}

/**
 * Select an answer for current question
 */
function selectAnswer(choiceId) {
    userAnswers[currentQuestionIndex] = choiceId;
    displayQuestion();
}

/**
 * Navigate to next question
 */
function nextQuestion() {
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        displayQuestion();
    }
}

/**
 * Navigate to previous question
 */
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion();
    }
}

function updateNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');

    // Disable previous button on first question
    prevBtn.disabled = currentQuestionIndex === 0;

    // Show submit button on last question, otherwise show next
    if (currentQuestionIndex === questions.length - 1) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'block';
    } else {
        nextBtn.style.display = 'block';
        submitBtn.style.display = 'none';
    }
}

function updateProgress() {
    const answeredCount = userAnswers.filter(a => a !== null).length;
    const progress = (answeredCount / questions.length) * 100;
    document.getElementById('progress-fill').style.width = progress + '%';

    // Update score display
    document.getElementById('total-answered').textContent = answeredCount;
}

function updateQuestionCounter() {
    document.getElementById('current-question').textContent = currentQuestionIndex + 1;
}

function submitQuiz() {
    // Check if all questions are answered
    const unanswered = userAnswers.filter(a => a === null).length;

    if (unanswered > 0) {
        const confirmSubmit = confirm(
            `You have ${unanswered} unanswered question(s). Do you want to submit anyway?`
        );
        if (!confirmSubmit) {
            return;
        }
    }

    score = 0;
    questions.forEach((question, index) => {
        const userAnswer = userAnswers[index];
        const correctChoice = question.choices.find(c => c.isCorrect);

        if (userAnswer === correctChoice.id) {
            score++;
        }
    });

    showResults();
}

/**
 * Display quiz results
 */
function showResults() {
    document.getElementById('quiz-content').style.display = 'none';
    document.getElementById('results').style.display = 'block';

    const percentage = Math.round((score / questions.length) * 100);

    document.getElementById('final-score').textContent = score;
    document.getElementById('final-total').textContent = questions.length;
    document.getElementById('percentage').textContent = percentage;

    // Optional: Add performance message
    const performanceMsg = getPerformanceMessage(percentage);
    const resultsCard = document.querySelector('.results-card');
    const existingMsg = resultsCard.querySelector('.performance-message');

    if (!existingMsg) {
        const msgElement = document.createElement('p');
        msgElement.className = 'performance-message';
        msgElement.style.fontSize = '1.1em';
        msgElement.style.marginTop = '20px';
        msgElement.textContent = performanceMsg;
        resultsCard.insertBefore(msgElement, resultsCard.querySelector('button'));
    }
}

/**
 * Get performance message based on percentage
 */
function getPerformanceMessage(percentage) {
    if (percentage === 100) return '🎉 Perfect score! Excellent work!';
    if (percentage >= 80) return '👏 Great job! You did really well!';
    if (percentage >= 60) return '👍 Good effort! Keep it up!';
    if (percentage >= 40) return '💪 Not bad, but there\'s room for improvement!';
    return '📚 Keep studying and try again!';
}

/**
 * Restart the quiz
 */
function restartQuiz() {
    currentQuestionIndex = 0;
    userAnswers = new Array(questions.length).fill(null);
    score = 0;

    document.getElementById('results').style.display = 'none';
    document.getElementById('quiz-content').style.display = 'block';
    document.getElementById('score').textContent = 0;
    document.getElementById('total-answered').textContent = 0;

    displayQuestion();
}

/**
 * Show error message
 */
function showError(message) {
    const loading = document.getElementById('loading');
    loading.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Keyboard navigation
 */
document.addEventListener('keydown', function(event) {
    // Only handle keyboard if quiz is active
    if (document.getElementById('quiz-content').style.display === 'none') {
        return;
    }

    // Arrow keys for navigation
    if (event.key === 'ArrowLeft' && currentQuestionIndex > 0) {
        previousQuestion();
    } else if (event.key === 'ArrowRight' && currentQuestionIndex < questions.length - 1) {
        nextQuestion();
    }

    // Number keys (1-4) for selecting answers
    if (event.key >= '1' && event.key <= '4') {
        const choiceIndex = parseInt(event.key) - 1;
        const question = questions[currentQuestionIndex];
        if (question.choices[choiceIndex]) {
            selectAnswer(question.choices[choiceIndex].id);
        }
    }
});

/**
 * Initialize quiz when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    loadQuestions();
});

// Expose functions to global scope for inline onclick handlers
window.selectAnswer = selectAnswer;
window.nextQuestion = nextQuestion;
window.previousQuestion = previousQuestion;
window.submitQuiz = submitQuiz;
window.restartQuiz = restartQuiz;