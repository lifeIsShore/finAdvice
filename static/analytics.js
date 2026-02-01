// Analytics Page JavaScript - FIXED VERSION
// FIX #3: Proper confusion matrix rendering using bar charts instead of scatter

const ticker = document.getElementById('ticker-name').textContent;

async function loadDiagnostics() {
    try {
        const response = await fetch(`/api/model_diagnostics/${ticker}`);
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
        renderConfusionMatrices(data);  // FIXED
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
    const ctx = document.getElementById('roc-chart').getContext('2d');

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
            maintainAspectRatio: true,
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
    const ctx = document.getElementById('feature-chart').getContext('2d');

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
            maintainAspectRatio: true,
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
        const cm = data[key]?.confusion_matrix;
        if (!cm || cm.length === 0) {
            document.getElementById(canvasId).parentElement.innerHTML = '<p style="color: #a0aec0; text-align: center;">No data</p>';
            return;
        }

        // FIXED: Pass model name for better labeling
        renderConfusionMatrix(canvasId, cm, name);
    });
}

// FIXED: Proper confusion matrix visualization using bar chart
function renderConfusionMatrix(canvasId, matrix, modelName) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Matrix format: [[TN, FP], [FN, TP]]
    // Extract values
    const tn = matrix[0][0];  // True Negatives (Correct Down predictions)
    const fp = matrix[0][1];  // False Positives (Predicted Up but was Down)
    const fn = matrix[1][0];  // False Negatives (Predicted Down but was Up)
    const tp = matrix[1][1];  // True Positives (Correct Up predictions)

    // Create bar chart with 2x2 grid representation
    const labels = ['Predicted Down\n(Actual Down)', 'Predicted Up\n(Actual Down)', 
                    'Predicted Down\n(Actual Up)', 'Predicted Up\n(Actual Up)'];
    const values = [tn, fp, fn, tp];
    const colors = [
        'rgba(76, 175, 80, 0.7)',    // TN - Green (correct)
        'rgba(255, 152, 0, 0.7)',    // FP - Orange (false alarm)
        'rgba(244, 67, 54, 0.7)',    // FN - Red (miss)
        'rgba(76, 175, 80, 0.7)'     // TP - Green (correct)
    ];
    const borderColors = [
        '#4CAF50',    // TN
        '#FF9800',    // FP
        '#F44336',    // FN
        '#4CAF50'     // TP
    ];

    // Calculate max for scaling
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
            maintainAspectRatio: true,
            scales: {
                x: {
                    stacked: false,
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    beginAtZero: true,
                    max: Math.ceil(maxValue * 1.1),  // Add 10% padding
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#a0aec0', stepSize: 5 }
                }
            },
            plugins: {
                legend: { display: true, labels: { color: '#fff' } },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const idx = context.dataIndex;
                            const labels_info = [
                                'True Negatives - Correctly predicted DOWN',
                                'False Positives - Wrongly predicted UP',
                                'False Negatives - Wrongly predicted DOWN',
                                'True Positives - Correctly predicted UP'
                            ];
                            return labels_info[idx];
                        }
                    },
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#a0aec0'
                }
            }
        }
    });
}

function renderResidualPlot(data) {
    const ctx = document.getElementById('residual-chart').getContext('2d');

    // Use the best model's residuals (linear_regression as default)
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
            maintainAspectRatio: true,
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
