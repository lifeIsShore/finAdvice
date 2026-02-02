// Analytics Page JavaScript - UNIVERSAL VERSION
// Synchronized with frontend/js/analytics.js

// Dynamic API Base Detection
const getApiBaseUrl = () => {
    if (window.location.protocol !== 'file:') {
        return window.location.origin;
    }
    return 'http://127.0.0.1:5000';
};

const API_BASE_URL = getApiBaseUrl();

// Get ticker from URL or global variable
const currentTickerId = window.currentTicker || new URLSearchParams(window.location.search).get('ticker') || 'AAPL';

let currentCharts = [];

async function loadDiagnostics(interval = '1d') {
    try {
        // Reset view
        document.getElementById('loading').style.display = 'block';
        document.getElementById('content').style.display = 'none';
        document.getElementById('error').style.display = 'none';

        const response = await fetch(`${API_BASE_URL}/api/model_diagnostics/${currentTickerId}?interval=${interval}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        document.getElementById('loading').style.display = 'none';
        const content = document.getElementById('content');
        if (content) content.style.display = 'block';

        // Clear existing charts to prevent overlaps
        currentCharts.forEach(chart => chart.destroy());
        currentCharts = [];

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
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
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
            const accuracy = metrics.accuracy || (metrics.direction_accuracy) || 0;

            row.innerHTML = `
                <td><strong>${modelNames[model]}</strong></td>
                <td>${accuracy.toFixed(1)}%</td>
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

    const chart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { type: 'linear', title: { display: true, text: 'False Positive Rate' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                y: { type: 'linear', title: { display: true, text: 'True Positive Rate' }, grid: { color: 'rgba(255,255,255,0.1)' } }
            }
        }
    });
    currentCharts.push(chart);
}

function renderFeatureImportance(data) {
    const canvas = document.getElementById('feature-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let featureData = data.random_forest?.feature_importance || data.xgboost?.feature_importance;
    if (!featureData || featureData.length === 0) return;

    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: featureData.map(f => f.feature),
            datasets: [{ label: 'Importance', data: featureData.map(f => f.importance), backgroundColor: 'rgba(102, 126, 234, 0.6)' }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false }
    });
    currentCharts.push(chart);
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
        if (!cm || cm.length === 0) return;
        renderConfusionMatrix(canvasId, cm, name);
    });
}

function renderConfusionMatrix(canvasId, matrix, modelName) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const ctx = el.getContext('2d');
    const labels = ['Predicted Down (Actual Down)', 'Predicted Up (Actual Down)', 'Predicted Down (Actual Up)', 'Predicted Up (Actual Up)'];
    const values = [matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1]];

    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{ label: 'Count', data: values, backgroundColor: ['#4CAF50', '#FF9800', '#F44336', '#4CAF50'] }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
    currentCharts.push(chart);
}

function renderResidualPlot(data) {
    const canvas = document.getElementById('residual-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const residuals = data.linear_regression?.residuals;
    if (!residuals || !residuals.actual) return;

    const points = residuals.actual.map((actual, i) => ({ x: residuals.predicted[i], y: residuals.residuals[i] }));
    const chart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{ label: 'Residuals', data: points, backgroundColor: 'rgba(102, 126, 234, 0.5)' }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
    currentCharts.push(chart);
}

// Handle Interval Change
document.getElementById('interval-select')?.addEventListener('change', (e) => {
    loadDiagnostics(e.target.value);
});

loadDiagnostics();
