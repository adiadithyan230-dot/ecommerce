// Dashboard Plotting Module
function renderDashboardCharts() {
    const charts = [
        { id: 'monthlyTrendChart', dataId: 'monthly-trend-json' },
        { id: 'categoryRevChart', dataId: 'category-rev-json' },
        { id: 'regionRevChart', dataId: 'region-rev-json' },
        { id: 'paymentMethodsChart', dataId: 'payment-methods-json' },
        { id: 'orderStatusChart', dataId: 'order-status-json' },
        { id: 'topProductsChart', dataId: 'top-products-json' },
        { id: 'dailyTrendChart', dataId: 'daily-trend-json' },
        { id: 'heatmapChart', dataId: 'heatmap-json' }
    ];

    charts.forEach(chart => {
        const dataElem = document.getElementById(chart.dataId);
        const container = document.getElementById(chart.id);
        if (dataElem && container) {
            try {
                const chartJson = JSON.parse(dataElem.textContent);
                if (chartJson && Object.keys(chartJson).length > 0) {
                    Plotly.newPlot(chart.id, chartJson.data, chartJson.layout, { 
                        responsive: true, 
                        displayModeBar: true, 
                        displaylogo: false,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d']
                    }).then(() => {
                        if (window.refreshPlotlyTheme) {
                            window.refreshPlotlyTheme(document.documentElement.getAttribute('data-theme') || 'light');
                        }
                    });
                } else {
                    container.innerHTML = '<div class="text-muted text-center py-5">No metrics for active filter</div>';
                }
            } catch (err) {
                console.error("Error loading plot: " + chart.id, err);
                container.innerHTML = '<div class="text-danger text-center py-5">Rendering failure</div>';
            }
        }
    });
}

// Hook HTMX request lifecycle to re-render charts when page contents are updated via AJAX
document.addEventListener('DOMContentLoaded', () => {
    renderDashboardCharts();

    document.body.addEventListener('submit', (evt) => {
        const form = evt.target.closest('.ai-insight-form');
        if (!form) {
            return;
        }

        const button = form.querySelector('.ai-insight-submit');
        if (!button) {
            return;
        }

        button.disabled = true;
        const label = button.querySelector('.ai-insight-label');
        const loading = button.querySelector('.ai-insight-loading');
        if (label && loading) {
            label.classList.add('d-none');
            loading.classList.remove('d-none');
        }
    });

    // Trigger on HTMX swapping
    document.body.addEventListener('htmx:afterSwap', (evt) => {
        renderDashboardCharts();
    });

    document.addEventListener('theme:changed', (evt) => {
        if (window.refreshPlotlyTheme) {
            window.refreshPlotlyTheme(evt.detail.theme);
        }
    });
});
