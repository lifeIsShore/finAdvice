// Analytics Page JavaScript - FIXED VERSION
// Synchronized with frontend/js/analytics.js

const API_BASE_URL = window.location.origin;

// Get ticker from URL or global variable
const ticker = window.currentTicker || new URLSearchParams(window.location.search).get('ticker');

async function loadDiagnostics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/model_diagnostics/${ticker}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';

        // Render all visualizations
        renderExtendedMetrics(data);
        renderROCCurves(data);
        renderFeatureImportance(data);
        renderConfusionMatrices(data);
        renderResidualPlot(data);

    } catch (error) {
        showError('Failed to load diagnostics: ' + error.message);
    }
}

function showError(message) {
    document.getElementById('loading').style.display = 'none';
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function renderExtendedMetrics(data) {
    const tbody = document.querySelector('#extended-metrics tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const models = ['linear_regression', 'random_forest', 'xgboost'];
    const modelNames = { 'linear_regression': 'Linear Regression', 'random_forest': 'Random Forest', 'xgboost': 'XGBoost' };

    models.forEach(model => {
        if (data[model] && data[model].classification_metrics) {
            const metrics = data[model].classification_metrics;
            const roc = data[model].roc_curve || {};

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${modelNames[model]}</strong></td>
                <td>${(metrics.precision * 100).toFixed(1)}%</td>
                <td>${(metrics.recall * 100).toFixed(1)}%</td>
                <td>${(metrics.f1_score * 100).toFixed(1)}%</td>
                <td>${(roc.auc || 0.5).toFixed(3)}</td>
            `;
            tbody.appendChild(row);
        }
    });
}

function renderROCCurves(data) {
    const canvas = document.getElementById('roc-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const datasets = [];
    const models = ['linear_regression', 'random_forest', 'xgboost'];
    const colors = ['#667eea', '#f093fb', '#4facfe'];
    const modelNames = { 'linear_regression': 'Linear Regression', 'random_forest': 'Random Forest', 'xgboost': 'XGBoost' };

    models.forEach((model, idx) => {
        if (data[model] && data[model].roc_curve) {
            const roc = data[model].roc_curve;
            const points = roc.fpr.map((fpr, i) => ({ x: fpr, y: roc.tpr[i] }));

            datasets.push({
                label: `${modelNames[model]} (AUC: ${roc.auc.toFixed(3)})`,
                data: points,
                borderColor: colors[idx],
                backgroundColor: colors[idx] + '20',
                borderWidth: 2,
                pointRadius: 0,
                fill: false
            });
        }
    });

    // Add diagonal reference line
    datasets.push({
        label: 'Random Guess',
        data: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
        borderColor: '#666',
        borderDash: [5, 5],
        borderWidth: 1,
        pointRadius: 0,
        fill: false
    });

    new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    title: { display: true, text: 'False Positive Rate', color: '#a0aec0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    type: 'linear',
                    title: { display: true, text: 'True Positive Rate', color: '#a0aec0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { labels: { color: '#fff' } }
            }
        }
    });
}

function renderFeatureImportance(data) {
    const canvas = document.getElementById('feature-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Use Random Forest or XGBoost (whichever has feature importance)
    let featureData = data.random_forest?.feature_importance || data.xgboost?.feature_importance;

    if (!featureData || featureData.length === 0) {
        ctx.canvas.parentElement.innerHTML = '<p style="color: #a0aec0; text-align: center;">No feature importance data available</p>';
        return;
    }

    const labels = featureData.map(f => f.feature);
    const values = featureData.map(f => f.importance);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Importance',
                data: values,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: '#667eea',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderConfusionMatrices(data) {
    const models = [
        { key: 'linear_regression', canvasId: 'cm-lr', name: 'Linear Regression' },
        { key: 'random_forest', canvasId: 'cm-rf', name: 'Random Forest' },
        { key: 'xgboost', canvasId: 'cm-xgb', name: 'XGBoost' }
    ];

    models.forEach(({ key, canvasId, name }) => {
        const el = document.getElementById(canvasId);
        if (!el) return;
        const cm = data[key]?.confusion_matrix;
        if (!cm || cm.length === 0) {
            el.parentElement.innerHTML = '<p style="color: #a0aec0; text-align: center;">No data</p>';
            return;
        }

        renderConfusionMatrix(canvasId, cm, name);
    });
}

function renderConfusionMatrix(canvasId, matrix, modelName) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const ctx = el.getContext('2d');

    // Matrix format: [[TN, FP], [FN, TP]]
    const tn = matrix[0][0];
    const fp = matrix[0][1];
    const fn = matrix[1][0];
    const tp = matrix[1][1];

    const labels = ['Predicted Down\n(Actual Down)', 'Predicted Up\n(Actual Down)',
        'Predicted Down\n(Actual Up)', 'Predicted Up\n(Actual Up)'];
    const values = [tn, fp, fn, tp];
    const colors = [
        'rgba(76, 175, 80, 0.7)',
        'rgba(255, 152, 0, 0.7)',
        'rgba(244, 67, 54, 0.7)',
        'rgba(76, 175, 80, 0.7)'
    ];
    const borderColors = ['#4CAF50', '#FF9800', '#F44336', '#4CAF50'];

    const maxValue = Math.max(...values);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: false,
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    beginAtZero: true,
                    max: Math.ceil(maxValue * 1.1) || 10,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderResidualPlot(data) {
    const canvas = document.getElementById('residual-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const residuals = data.linear_regression?.residuals;

    if (!residuals || !residuals.actual) {
        ctx.canvas.parentElement.innerHTML = '<p style="color: #a0aec0; text-align: center;">No residual data available</p>';
        return;
    }

    const points = residuals.actual.map((actual, i) => ({
        x: residuals.predicted[i],
        y: residuals.residuals[i]
    }));

    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Residuals',
                data: points,
                backgroundColor: 'rgba(102, 126, 234, 0.5)',
                borderColor: '#667eea',
                pointRadius: 4
            }, {
                label: 'Zero Line',
                type: 'line',
                data: [{ x: Math.min(...residuals.predicted), y: 0 }, { x: Math.max(...residuals.predicted), y: 0 }],
                borderColor: '#ff6b6b',
                borderDash: [5, 5],
                borderWidth: 2,
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Predicted Values', color: '#a0aec0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    title: { display: true, text: 'Residuals', color: '#a0aec0' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { labels: { color: '#fff' } }
            }
        }
    });
}

// Load diagnostics on page load
loadDiagnostics();
