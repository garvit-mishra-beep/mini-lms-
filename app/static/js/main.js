/**
 * MiniLMS Modern JavaScript Controller
 * Handles Theme Toggling, Mobile Sidebar, Flash Auto-dismiss, and Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme (Dark / Light Mode) Persistence
  const savedTheme = localStorage.getItem('minilms-theme') || 
                     (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('minilms-theme', nextTheme);
      updateThemeIcon(nextTheme);
    });
  }

  function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (!icon) return;
    if (theme === 'dark') {
      icon.innerHTML = '&#9728;'; // Sun symbol
      icon.setAttribute('title', 'Switch to Light Mode');
    } else {
      icon.innerHTML = '&#9790;'; // Moon symbol
      icon.setAttribute('title', 'Switch to Dark Mode');
    }
  }

  // 2. Mobile Sidebar Toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const sidebar = document.getElementById('app-sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && 
          !sidebar.contains(e.target) && 
          e.target !== mobileToggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  // 3. Auto-dismiss Flash Alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });

  // 4. Quick Table Filter (client-side dynamic search where marked with data-table-filter)
  const quickSearchInputs = document.querySelectorAll('[data-table-search]');
  quickSearchInputs.forEach(input => {
    const targetTableId = input.getAttribute('data-table-search');
    const table = document.getElementById(targetTableId);
    if (!table) return;

    input.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  });

  // 5. Destructive Action Confirmation
  const confirmForms = document.querySelectorAll('form[data-confirm]');
  confirmForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const msg = form.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});
