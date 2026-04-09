/* ============================================================
   DASHBOARD.JS — Delete account modal & OTP flow
   ============================================================ */

// ── Modal open / close ──────────────────────────────────────

function showDeleteModal() {
  var m = document.getElementById('delete-modal');
  m.style.display = 'flex';
  var pw = m.querySelector('input[type=password]');
  if (pw) { pw.focus(); }
}

function hideDeleteModal() {
  var m = document.getElementById('delete-modal');
  m.style.display = 'none';

  // Reset OTP flow back to step 1 for next open
  var s1 = document.getElementById('otp-step-1');
  var s2 = document.getElementById('otp-step-2');
  if (s1) { s1.style.display = ''; }
  if (s2) { s2.style.display = 'none'; }

  var otpInput = document.getElementById('otp-input');
  if (otpInput) { otpInput.value = ''; }

  var pw = m.querySelector('input[type=password]');
  if (pw) { pw.value = ''; }
}

// ── OTP send via fetch (no page reload) ────────────────────

function getCsrfToken() {
  var el = document.querySelector('[name=csrfmiddlewaretoken]');
  return el ? el.value : '';
}

function sendOtp() {
  var btn    = document.getElementById('send-otp-btn');
  var errBox = document.getElementById('otp-send-error');
  var otpUrl = btn.dataset.url;

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending…';
  errBox.style.display = 'none';

  fetch(otpUrl, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
  .then(function (res) {
    if (res.ok) {
      document.getElementById('otp-step-1').style.display = 'none';
      document.getElementById('otp-step-2').style.display = '';
      setTimeout(function () {
        var inp = document.getElementById('otp-input');
        if (inp) { inp.focus(); }
      }, 50);
    } else {
      throw new Error('Server error ' + res.status);
    }
  })
  .catch(function () {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Code';
    errBox.textContent = 'Failed to send the code. Please try again later.';
    errBox.style.display = 'block';
  });
}

function resendOtp() {
  document.getElementById('otp-step-2').style.display = 'none';
  document.getElementById('otp-step-1').style.display = '';
  var btn = document.getElementById('send-otp-btn');
  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Code';
  sendOtp();
}

// ── Init ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  // Close on backdrop click
  var modal = document.getElementById('delete-modal');
  if (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === this) { hideDeleteModal(); }
    });
  }
});