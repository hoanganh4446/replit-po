document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.style.display = 'none';
    overlay.style.position = 'fixed';
    overlay.style.inset = '0';
    overlay.style.background = 'rgba(0,0,0,0.55)';
    overlay.style.zIndex = '999';
    document.body.appendChild(overlay);

    const closeSidebar = () => {
        if (sidebar) sidebar.classList.remove('open');
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    };

    const openSidebar = () => {
        if (sidebar) sidebar.classList.add('open');
        overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';
    };

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            if (sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    overlay.addEventListener('click', closeSidebar);

    document.addEventListener('keyup', (event) => {
        if (event.key === 'Escape') {
            closeSidebar();
        }
    });

    // Header shadow on scroll
    const appMain = document.querySelector('.app-main');
    if (appMain) {
        appMain.addEventListener('scroll', () => {
            const header = document.querySelector('.app-header');
            if (!header) return;
            if (appMain.scrollTop > 10) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }
});
