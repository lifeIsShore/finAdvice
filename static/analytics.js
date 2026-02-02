// Analytics Page JavaScript - Multi-Interval Version

const API_BASE_URL = window.location.origin;

// Get ticker from URL or global variable
const ticker = window.currentTicker || new URLSearchParams(window.location.search).get('ticker');

// Global data store
let consensusData = {};
let currentInterval = '1d';

async function loadDiagnostics() {
    try {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('content').style.display = 'none';

        const response = await fetch(`${API_BASE_URL}/api/model_diagnostics/${ticker}`);
        const data = await response.json();

        if (data.error || Object.keys(data).length === 0) {
            showError("No model data found for " + ticker);
            return;
        }

        consensusData = data;

        // Initialize UI with available intervals
        setupIntervalTabs(Object.keys(data));

        // Render default interval
        if (!consensusData['1d']) {
            currentInterval = Object.keys(consensusData)[0];
        } else {
            currentInterval = '1d';
        }

        updateDashboard();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';

    } catch (error) {
        showError('Failed to load data: ' + error.message);
    }
}

function showError(message) {
    document.getElementById('loading').style.display = 'none';
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function setupIntervalTabs(intervals) {
    const container = document.getElementById('interval-tabs');
    if (!container) return; // Guard if element doesn't exist yet (will look for it later)

    container.innerHTML = '';

    const order = ['1h', '4h', '1d', '1wk', '1mo'];
    // Sort intervals based on preferred order
    intervals.sort((a, b) => {
        return order.indexOf(a) - order.indexOf(b);
    });

    intervals.forEach(inv => {
        const btn = document.createElement('button');
        btn.className = `tab-btn ${inv === currentInterval ? 'active' : ''}`;
        btn.textContent = inv.toUpperCase();
        btn.onclick = () => {
            currentInterval = inv;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateDashboard();
        };
        container.appendChild(btn);
    });
}

function updateDashboard() {
    const data = consensusData[currentInterval];
    if (!data) return;

    renderSummary(data);
    renderMetricsTable(data);
    renderComparisonCharts(data);
}

function renderSummary(data) {
    const winnerEl = document.getElementById('interval-winner');
    const sentimentEl = document.getElementById('interval-sentiment');

    if (winnerEl) winnerEl.textContent = (data.best_model || 'Unknown').toUpperCase();
    if (sentimentEl) {
        sentimentEl.textContent = `${data.sentiment_emoji} ${data.sentiment_label} (${data.change_percent > 0 ? '+' : ''}${data.change_percent}%)`;
        sentimentEl.style.color = data.sentiment_color || '#fff';
    }
}

function renderMetricsTable(data) {
    const tbody = document.querySelector('#extended-metrics tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const models = data.models || [];

    // Sort by accuracy descending
    models.sort((a, b) => b.accuracy - a.accuracy);

    models.forEach(m => {
        const row = document.createElement('tr');
        const isWinner = m.model_name === data.best_model;

        row.innerHTML = `
            <td>
                <strong>${m.model_name}</strong>
                ${isWinner ? '<span class="badge winner">WINNER</span>' : ''}
            </td>
            <td>${m.accuracy.toFixed(1)}%</td>
            <td>${m.rmse.toFixed(4)}</td>
            <td>${m.r2_score.toFixed(4)}</td>
            <td>${m.mape.toFixed(1)}%</td>
        `;
        if (isWinner) row.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        tbody.appendChild(row);
    });
}

function renderComparisonCharts(data) {
    const ctx = document.getElementById('roc-chart'); // Reusing ID for simplicity, but it's now Model Comparison
    if (!ctx) return;

    // Destroy previous chart if exists
    const chartStatus = Chart.getChart("roc-chart");
    if (chartStatus != undefined) {
        chartStatus.destroy();
    }

    const models = data.models || [];
    const labels = models.map(m => m.model_name);
    const accuracy = models.map(m => m.accuracy);
    const rmse = models.map(m => m.rmse);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Accuracy (%)',
                    data: accuracy,
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'RMSE (Lower is Better)',
                    data: rmse,
                    backgroundColor: 'rgba(245, 158, 11, 0.6)',
                    borderColor: '#f59e0b',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Accuracy' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'RMSE' },
                    grid: { drawOnChartArea: false }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Model Performance Comparison',
                    color: '#fff',
                    font: { size: 16 }
                }
            }
        }
    });
}

// Just trigger load
loadDiagnostics();
