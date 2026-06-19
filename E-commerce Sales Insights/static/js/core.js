// Global Javascript Utilities
document.addEventListener('DOMContentLoaded', () => {
    // Theme Switcher Logic
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    
    // Check saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);
    htmlElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);
    refreshPlotlyTheme(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlElement.setAttribute('data-theme', newTheme);
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            refreshPlotlyTheme(newTheme);
            document.dispatchEvent(new CustomEvent('theme:changed', { detail: { theme: newTheme } }));
        });
    }

    function updateThemeIcon(theme) {
        const icon = document.querySelector('#theme-toggle i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun';
            } else {
                icon.className = 'fas fa-moon';
            }
        }
    }

    function refreshPlotlyTheme(theme) {
        if (!window.Plotly) {
            return;
        }

        const isDark = theme === 'dark';
        const fontColor = isDark ? '#d7e0ef' : '#475569';
        const gridColor = isDark ? '#26344a' : '#e2e8f0';

        document.querySelectorAll('.js-plotly-plot').forEach(plot => {
            Plotly.relayout(plot, {
                'font.color': fontColor,
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'plot_bgcolor': 'rgba(0,0,0,0)',
                'xaxis.gridcolor': gridColor,
                'yaxis.gridcolor': gridColor,
                'xaxis.zerolinecolor': gridColor,
                'yaxis.zerolinecolor': gridColor
            });
        });
    }

    window.refreshPlotlyTheme = refreshPlotlyTheme;

    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);
});
