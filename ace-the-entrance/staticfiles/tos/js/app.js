/* ============================================================
   APP.JS — TOS page: tab switching + sidebar/mobile TOC builder
   ============================================================ */

const tosSections = [
  { id: 'tos-acceptance',  label: 'Acceptance of Terms' },
  { id: 'tos-use',         label: 'Use of Services' },
  { id: 'tos-accounts',    label: 'User Accounts' },
  { id: 'tos-ip',          label: 'Intellectual Property' },
  { id: 'tos-disclaimer',  label: 'Disclaimer' },
  { id: 'tos-liability',   label: 'Limitation of Liability' },
  { id: 'tos-termination', label: 'Termination' },
  { id: 'tos-governing',   label: 'Governing Law' },
];

const prvSections = [
  { id: 'prv-intro',     label: 'Introduction' },
  { id: 'prv-collect',   label: 'Information We Collect' },
  { id: 'prv-use',       label: 'How We Use It' },
  { id: 'prv-sharing',   label: 'Sharing Your Data' },
  { id: 'prv-cookies',   label: 'Cookies' },
  { id: 'prv-rights',    label: 'Your Rights' },
  { id: 'prv-security',  label: 'Data Security' },
  { id: 'prv-retention', label: 'Data Retention' },
  { id: 'prv-children',  label: "Children's Privacy" },
  { id: 'prv-changes',   label: 'Changes to Policy' },
];

let currentTab = 'tos';

// ── TOC builder ─────────────────────────────────────────────

function buildSidebar(sections) {
  const html = sections.map(s =>
    `<li><a href="#${s.id}">${s.label}</a></li>`
  ).join('');

  // Desktop sidebar
  const sidebarNav = document.getElementById('sidebar-nav');
  if (sidebarNav) { sidebarNav.innerHTML = html; }

  // Mobile TOC — same links, close drawer on click
  const mobileTocNav = document.getElementById('mobile-toc-nav');
  if (mobileTocNav) {
    mobileTocNav.innerHTML = html;
    mobileTocNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMobileToc);
    });
  }
}

// ── Tab switching ────────────────────────────────────────────

function switchTab(tab, btn) {
  currentTab = tab;
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });
  document.getElementById(tab).classList.add('active');
  btn.classList.add('active');
  btn.setAttribute('aria-selected', 'true');
  buildSidebar(tab === 'tos' ? tosSections : prvSections);

  // Close mobile TOC when switching tabs
  closeMobileToc();
}

// ── Mobile TOC open / close ──────────────────────────────────

function toggleMobileToc() {
  const toc    = document.getElementById('mobile-toc');
  const toggle = document.getElementById('toc-toggle');
  const isOpen = toc.classList.contains('visible');

  toc.classList.toggle('visible', !isOpen);
  toggle.classList.toggle('open', !isOpen);
  toggle.setAttribute('aria-expanded', String(!isOpen));
  toc.setAttribute('aria-hidden', String(isOpen));
}

function closeMobileToc() {
  const toc    = document.getElementById('mobile-toc');
  const toggle = document.getElementById('toc-toggle');
  if (!toc || !toggle) { return; }
  toc.classList.remove('visible');
  toggle.classList.remove('open');
  toggle.setAttribute('aria-expanded', 'false');
  toc.setAttribute('aria-hidden', 'true');
}

// ── Init ─────────────────────────────────────────────────────

buildSidebar(tosSections);