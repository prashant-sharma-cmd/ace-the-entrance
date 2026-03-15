/* ============================================================
   quiz/modal.js  –  Lightweight modal utility
   Usage:
     QuizModal.confirm({
       id:       'myModal',        // id of the .qmodal-backdrop element
       icon:     '🚀',
       title:    'Are you sure?',
       body:     'This cannot be undone.',
       confirm:  'Yes, do it',
       cancel:   'Go back',
       danger:   false,            // true → red confirm button
       onConfirm: function() { ... }
     });

   Or to open/close manually:
     QuizModal.open('myModalId');
     QuizModal.close('myModalId');
   ============================================================ */



(function (global) {
    'use strict';

    /* ── Low-level open / close ── */
    function open(id) {
        var el = document.getElementById(id);
        if (el) el.classList.add('open');
    }

    function close(id) {
        var el = document.getElementById(id);
        if (el) el.classList.remove('open');
    }

    /* ── Close on backdrop click or Escape ── */
    document.addEventListener('click', function (e) {
        if (e.target && e.target.classList.contains('qmodal-backdrop')) {
            e.target.classList.remove('open');
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.qmodal-backdrop.open').forEach(function (el) {
                el.classList.remove('open');
            });
        }
    });

    /* ── Dynamic modal builder ── */
    function confirm(opts) {
        var id         = opts.id || ('qmodal-' + Date.now());
        var icon       = opts.icon    || '❓';
        var title      = opts.title   || 'Are you sure?';
        var body       = opts.body    || '';
        var confirmTxt = opts.confirm || 'Confirm';
        var cancelTxt  = opts.cancel  || 'Cancel';
        var danger     = opts.danger  || false;
        var onConfirm  = opts.onConfirm || function () {};

        /* Re-use existing backdrop if it already exists */
        var existing = document.getElementById(id);
        if (existing) existing.remove();

        var backdrop = document.createElement('div');
        backdrop.className  = 'qmodal-backdrop';
        backdrop.id         = id;
        backdrop.setAttribute('role', 'dialog');
        backdrop.setAttribute('aria-modal', 'true');

        backdrop.innerHTML =
            '<div class="qmodal">' +
                '<span class="qmodal-icon">' + icon + '</span>' +
                '<div class="qmodal-title">' + title + '</div>' +
                '<div class="qmodal-body">'  + body  + '</div>' +
                '<div class="qmodal-actions">' +
                    '<button class="qmodal-btn qmodal-btn-cancel"  id="' + id + '-cancel">'  + cancelTxt  + '</button>' +
                    '<button class="qmodal-btn ' + (danger ? 'qmodal-btn-danger' : 'qmodal-btn-confirm') + '" id="' + id + '-confirm">' + confirmTxt + '</button>' +
                '</div>' +
            '</div>';

        document.body.appendChild(backdrop);

        document.getElementById(id + '-cancel').addEventListener('click', function () {
            close(id);
        });

        document.getElementById(id + '-confirm').addEventListener('click', function () {
            close(id);
            onConfirm();
        });

        /* Small delay so the element is in the DOM before transition fires */
        requestAnimationFrame(function () {
            requestAnimationFrame(function () { open(id); });
        });
    }

    global.QuizModal = { open: open, close: close, confirm: confirm };

}(window));