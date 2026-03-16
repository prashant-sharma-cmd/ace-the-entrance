document.addEventListener('DOMContentLoaded', function () {

  var btn         = document.getElementById('phoneCountryBtn');
  var dropdown    = document.getElementById('phoneDropdown');
  var flagEl      = document.getElementById('phoneFlag');
  var dialEl      = document.getElementById('phoneDialCode');
  var localInput  = document.getElementById('id_phone_local');
  var hiddenInput = document.getElementById('id_phone_number');
  var currentDial = '+977';

  // ── Seed local input on error re-render ──────────────────────────────────
  // If the server round-tripped a value like +9779812345678, strip the dial
  // prefix back out so the user only sees their local digits again.
  // This is what prevented the double-prefix on re-submit.
  (function seedLocalInput() {
    var stored = (hiddenInput.value || '').trim();
    if (!stored) return;

    var options = dropdown.querySelectorAll('.phone-option');
    var matched = false;

    // Sort by dial length descending so +977 matches before +9 (if it existed)
    var sorted = Array.prototype.slice.call(options).sort(function(a, b) {
      return b.dataset.dial.length - a.dataset.dial.length;
    });

    sorted.forEach(function (opt) {
      if (matched) return;
      if (stored.startsWith(opt.dataset.dial)) {
        currentDial = opt.dataset.dial;
        flagEl.textContent = opt.dataset.flag;
        dialEl.textContent = currentDial;
        options.forEach(function(o) { o.classList.remove('is-selected'); });
        opt.classList.add('is-selected');
        // Show only the local part (strip leading zeros Nepali users might have typed)
        localInput.value = stored.slice(opt.dataset.dial.length).replace(/^0+/, '');
        matched = true;
      }
    });

    if (!matched) {
      // Unknown format — show raw value and let user correct it
      localInput.value = stored.startsWith('+') ? stored.slice(1) : stored;
    }
  })();

  // ── Open / close dropdown ─────────────────────────────────────────────────
  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    var isOpen = dropdown.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(isOpen));
  });

  document.addEventListener('click', function () {
    dropdown.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  });

  // ── Select a country ──────────────────────────────────────────────────────
  dropdown.querySelectorAll('.phone-option').forEach(function (opt) {
    opt.addEventListener('click', function (e) {
      e.stopPropagation();
      currentDial = opt.dataset.dial;
      flagEl.textContent = opt.dataset.flag;
      dialEl.textContent = currentDial;

      dropdown.querySelectorAll('.phone-option').forEach(function (o) {
        o.classList.remove('is-selected');
      });
      opt.classList.add('is-selected');

      dropdown.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      localInput.focus();
    });
  });

  // ── On submit: build E.164 into the hidden field exactly once ─────────────
  // The local input is never POSTed directly, so no double-prefix can occur.
  document.getElementById('signup-form').addEventListener('submit', function () {
    var raw = localInput.value.trim();

    if (!raw) {
      hiddenInput.value = '';   // field left blank — valid (optional)
      return;
    }

    if (raw.startsWith('+')) {
      // User pasted a full international number — use as-is
      hiddenInput.value = raw;
      return;
    }

    // Strip any leading zeros (e.g. 0981234567 → 981234567)
    raw = raw.replace(/^0+/, '');
    hiddenInput.value = currentDial + raw;
  });

  // ── Password helpers ──────────────────────────────────────────────────────
  initStrengthMeter('id_password1', 'pw-strength-bar', 'pw-strength-label');
  initPasswordMatch('id_password1', 'id_password2', 'pw-match-error', 'signup-btn');
  initLoadingSubmit('signup-form', 'signup-btn', 'Creating account…');
});