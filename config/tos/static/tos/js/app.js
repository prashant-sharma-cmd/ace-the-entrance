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

    function buildSidebar(sections) {
      const nav = document.getElementById('sidebar-nav');
      nav.innerHTML = sections.map(s =>
        `<li><a href="#${s.id}">${s.label}</a></li>`
      ).join('');
    }

    function switchTab(tab, btn) {
      currentTab = tab;
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
      document.getElementById(tab).classList.add('active');
      btn.classList.add('active');
      btn.setAttribute('aria-selected','true');
      buildSidebar(tab === 'tos' ? tosSections : prvSections);
    }

    buildSidebar(tosSections);