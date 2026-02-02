let priceChart = null;

const API_BASE_URL = 'http://127.0.0.1:5000'; // Define the API base URL

// User-friendly error messages
const USER_FRIENDLY_ERRORS = {
    'No data found': {
        title: 'No Data Available',
        message: 'This ticker hasn\'t been analyzed yet.',
        action: 'Click "Sync Data" to download price history and start analysis.'
    },
    'No results found': {
        title: 'No Predictions Yet',
        message: 'AI predictions haven\'t been generated for this ticker.',
        action: 'Click "Predict" to run the analysis (takes ~30 seconds).'
    },
    'Failed to fetch': {
        title: 'Connection Error',
        message: 'Unable to reach the server.',
        action: 'Check your internet connection and try again.'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Show welcome modal for first-time users (if modal exists)
    const welcomeModal = document.getElementById('welcome-modal');
    if (welcomeModal && !localStorage.getItem('welcomed')) {
        welcomeModal.classList.remove('hidden');
    }

    // Check for ticker in URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlTicker = urlParams.get('ticker');

    loadTickers(urlTicker);

    const tickerSelect = document.getElementById('ticker-select');
    const runPipelineBtn = document.getElementById('run-pipeline');
    const runMLBtn = document.getElementById('run-ml');

    const getActiveTicker = () => {
        const custom = document.getElementById('custom-ticker').value.trim().toUpperCase();
        return custom || tickerSelect.value;
    };

    tickerSelect.addEventListener('change', () => {
        document.getElementById('custom-ticker').value = ''; // Clear custom if dropdown used
        updateDashboard(tickerSelect.value);
    });

    // Add event listener for custom ticker input
    const customTickerInput = document.getElementById('custom-ticker');
    customTickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const ticker = customTickerInput.value.trim().toUpperCase();
            if (ticker) {
                // Check if ticker exists in dropdown
                const options = [...tickerSelect.options];
                const matchingOption = options.find(opt => opt.value === ticker);
                if (matchingOption) {
                    tickerSelect.value = ticker;
                    customTickerInput.value = '';
                    updateDashboard(ticker);
                } else {
                    logConsole(`Ticker ${ticker} not found. Please sync data first.`);
                }
            }
        }
    });

    runPipelineBtn.addEventListener('click', async () => {
        const ticker = getActiveTicker();
        if (!ticker) return logConsole("Please select or enter a ticker.");

        showLoading("Fetching market data...", 0);
        logConsole(`Starting Pipeline for ${ticker}...`);

        try {
            // Step 1: Fetch raw data
            updateLoadingProgress("Downloading price history...", 30);
            const resp = await fetch(`${API_BASE_URL}/api/run_pipeline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker })
            });
            const data = await resp.json();
            logConsole("✓ Data fetched successfully");

            // Step 2: Run ML predictions
            updateLoadingProgress("Training AI model...", 60);
            logConsole(`Running ML predictions for ${ticker}...`);
            const horizon = document.getElementById('param-horizon').value;
            const risk = document.getElementById('param-risk').value;

            const mlResp = await fetch(`${API_BASE_URL}/api/run_ml`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker, horizon, risk })
            });
            const mlData = await mlResp.json();

            updateLoadingProgress("Finalizing predictions...", 90);
            logConsole("✓ ML predictions complete");
            logConsole(mlData.output);

            // Step 3: Refresh
            updateLoadingProgress("Loading results...", 100);
            setTimeout(() => {
                hideLoading();
                window.location.href = `index.html?ticker=${ticker}`;
            }, 500);

        } catch (e) {
            hideLoading();
            logConsole(`Error: ${e.message}`);
            showError("Failed to complete analysis. Please try again.");
        }
    });

    runMLBtn.addEventListener('click', async () => {
        const ticker = getActiveTicker();
        const horizon = document.getElementById('param-horizon').value;
        const risk = document.getElementById('param-risk').value;

        showLoading("Running AI predictions...", 10);
        logConsole(`Predicting for ${ticker} | Horizon: ${horizon}d | Risk: ${risk}...`);

        try {
            updateLoadingProgress("Training model...", 50);
            const resp = await fetch(`${API_BASE_URL}/api/run_ml`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker, horizon, risk })
            });
            const data = await resp.json();

            updateLoadingProgress("Finalizing...", 90);
            logConsole(data.output);

            await loadTickers(ticker);
            hideLoading();
        } catch (e) {
            hideLoading();
            logConsole(`Error: ${e.message}`);
            showError("Prediction failed. Please try again.");
        }
    });
});

async function loadTickers(targetTicker) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickers`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const tickers = await response.json();

        if (tickers.error) throw new Error(tickers.error);

        const select = document.getElementById('ticker-select');
        // Selection priority: Target Ticker (from URL/Sync) > Current Selection > First item
        const currentVal = targetTicker || select.value;

        select.innerHTML = '';
        tickers.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t; opt.textContent = t;
            select.appendChild(opt);
        });

        if (currentVal && tickers.includes(currentVal)) {
            select.value = currentVal;
            updateDashboard(currentVal);
        } else if (tickers.length > 0) {
            updateDashboard(tickers[0]);
        }
    } catch (e) {
        console.error("Failed to load tickers:", e);
        logConsole(`Error loading assets: ${e.message}`);
    }
}

async function updateDashboard(ticker) {
    if (!ticker) return;

    // Sync dropdown if it matches
    const select = document.getElementById('ticker-select');
    const customInput = document.getElementById('custom-ticker');

    if (select.value !== ticker && [...select.options].some(o => o.value === ticker)) {
        select.value = ticker;
        customInput.value = ''; // Clear custom input when dropdown is synced
    } else if (!select.value || select.value !== ticker) {
        // If ticker not in dropdown, show it in custom input
        customInput.value = ticker;
    }

    document.getElementById('current-ticker').textContent = ticker;
    fetchSentiment(ticker);
    fetchModelMetrics(ticker);
    await fetchHistoryAndDrawChart(ticker);

    try {
        const response = await fetch(`${API_BASE_URL}/api/results/${ticker}`);
        const data = await response.json();
        if (data.error) {
            const errorInfo = USER_FRIENDLY_ERRORS[data.error] || {
                title: 'Error',
                message: data.error,
                action: 'Please try again or contact support.'
            };

            showErrorPanel(errorInfo);
            logConsole(`No ML results for ${ticker} yet. Click 'Predict' to train.`);
            clearMetrics();
            return;
        }

        // UI Updates - FIX: Added $ prefix to all price values
        document.getElementById('price-val').textContent = `$${data.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('get-in-val').textContent = `$${data.recommended_get_in.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('get-out-val').textContent = `$${data.recommended_get_out.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('stop-loss-val').textContent = `$${data.recommended_stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('gain-val').textContent = `${data.potential_gain.toFixed(2)}%`;

        // DEBUG: Log the values to console for verification
        console.log('Dashboard Values:', {
            current_price: data.current_price,
            recommended_get_in: data.recommended_get_in,
            recommended_get_out: data.recommended_get_out,
            recommended_stop_loss: data.recommended_stop_loss,
            potential_gain: data.potential_gain
        });

        // FIX: Changed from 'asset-type' to 'ticker-badge'
        const badge = document.getElementById('ticker-badge');
        badge.textContent = data.asset_type || 'STOCK';
        badge.style.color = data.asset_type === 'Crypto' ? 'var(--secondary)' : 'var(--primary)';

        // Confidence - with fallback
        const confidence = data.confidence_score !== undefined ? data.confidence_score : 0;
        document.getElementById('confidence-fill').style.width = `${confidence}%`;
        document.getElementById('confidence-pct').textContent = `${Math.round(confidence)}%`;

        if (confidence === 0) {
            logConsole(`⚠️ Warning: Confidence score is 0 for ${ticker}. This may indicate data issues.`);
        }

        // Consensus - Enhanced multi-timeframe display with sentiment
        const list = document.getElementById('consensus-details');
        if (list) {
            list.innerHTML = '';
            const consensus = data.consensus || {};
            const timeframes = ['1h', '4h', '1d', '1wk', '1mo'];

            timeframes.forEach(interval => {
                const prediction = consensus[interval];
                if (!prediction) return;

                // Handle both legacy string format and new object format
                let direction = 'NEUTRAL';
                let changePercent = 0;
                let confidence = data.confidence_score || 0;
                let bestModel = 'Ensemble';

                if (typeof prediction === 'string') {
                    direction = prediction;
                    changePercent = prediction === 'UP' ? 0.5 : -0.5;
                } else if (typeof prediction === 'object') {
                    direction = prediction.sentiment || prediction.direction || 'NEUTRAL';
                    changePercent = prediction.change_percent || 0;
                    confidence = prediction.confidence || confidence;
                    bestModel = prediction.best_model || 'Ensemble';
                }

                // Classify sentiment based on change percent
                let sentiment, emoji, color;
                if (changePercent > 2.0) {
                    sentiment = 'Dramatic ↑';
                    emoji = '📈';
                    color = '#27ae60';
                } else if (changePercent > 1.0) {
                    sentiment = 'Strong ↑';
                    emoji = '↗️';
                    color = '#2ecc71';
                } else if (changePercent > 0.2) {
                    sentiment = 'Up';
                    emoji = '📊';
                    color = '#3498db';
                } else if (changePercent > -0.2) {
                    sentiment = 'Neutral';
                    emoji = '➡️';
                    color = '#95a5a6';
                } else if (changePercent > -1.0) {
                    sentiment = 'Down';
                    emoji = '📉';
                    color = '#e74c3c';
                } else if (changePercent > -2.0) {
                    sentiment = 'Strong ↓';
                    emoji = '↙️';
                    color = '#c0392b';
                } else {
                    sentiment = 'Dramatic ↓';
                    emoji = '⬇️';
                    color = '#8b0000';
                }

                // Create row with color-coded sentiment
                const row = document.createElement('div');
                row.className = 'metric-row consensus-row';
                row.style.borderLeft = `4px solid ${color}`;
                row.style.paddingLeft = '12px';
                row.style.paddingRight = '8px';
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                row.style.alignItems = 'center';

                row.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                        <span style="font-weight: 600; min-width: 35px; color: #a0aec0;">${interval.toUpperCase()}</span>
                        <span style="color: ${color}; font-weight: 600; font-size: 1.1rem;">${emoji}</span>
                        <span style="color: ${color}; font-weight: 500;">${sentiment}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; text-align: right;">
                        <span style="color: ${color}; font-weight: 600; min-width: 35px;">
                            ${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%
                        </span>
                        <span style="color: #a0aec0; font-size: 0.8rem; min-width: 100px;">
                            ${Math.round(confidence)}% • ${bestModel}
                        </span>
                    </div>
                `;

                list.appendChild(row);
            });
        }




        // Model Metrics
        const perf = data.performance || { r2: 0, mae: 0, rmse: 0 };
        // These elements were in the HTML but removed in updated design? Or need to be there?
        // Let's check for existence first
        if (document.getElementById('metric-r2')) document.getElementById('metric-r2').textContent = (perf.r2 || 0).toFixed(4);
        if (document.getElementById('metric-mae')) document.getElementById('metric-mae').textContent = '$' + (perf.mae || 0).toFixed(2);
        if (document.getElementById('metric-rmse')) document.getElementById('metric-rmse').textContent = (perf.rmse || 0).toFixed(2);

        // Last Trained
        document.getElementById('last-trained').textContent = data.last_trained || '---';

        // Update winner explicitly if not already handled by fetchModelMetrics (fallback)
        if (data.model_competition && data.model_competition.winner) {
            document.getElementById('winner-name').textContent = data.model_competition.winner.toUpperCase();
        }

        // Display Market Sentiment
        if (data.market_sentiment && data.market_sentiment_label) {
            const sentimentBox = document.getElementById('market-sentiment-box');
            const sentimentIcon = document.getElementById('sentiment-icon');
            const sentimentLabel = document.getElementById('sentiment-label');
            const sentimentValue = document.getElementById('sentiment-value');

            sentimentBox.style.display = 'flex';

            // Map text icons back to emojis for UI
            const iconMap = {
                '[DRAMATICALLY_UP]': '📈',
                '[UP]': '↗️',
                '[SIDEWAYS]': '➡️',
                '[DOWN]': '↘️',
                '[DRAMATICALLY_DOWN]': '📉'
            };
            sentimentIcon.textContent = iconMap[data.market_sentiment_icon] || data.market_sentiment_icon || '➡️';
            sentimentLabel.textContent = 'Market Outlook';
            sentimentValue.textContent = data.market_sentiment_label;

            // Remove all sentiment classes
            sentimentValue.classList.remove('dramatically-up', 'up', 'sideways', 'down', 'dramatically-down');

            // Add appropriate class based on sentiment
            const sentimentClass = data.market_sentiment.toLowerCase().replace('_', '-');
            sentimentValue.classList.add(sentimentClass);
        }

        // Add predictions to chart if it exists
        if (priceChart) {
            priceChart.options.plugins.annotation = {
                annotations: {
                    getIn: {
                        type: 'line',
                        yMin: data.recommended_get_in,
                        yMax: data.recommended_get_in,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        label: {
                            content: 'BUY ' + data.recommended_get_in.toFixed(2),
                            enabled: true,
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            color: 'white'
                        }
                    },
                    getOut: {
                        type: 'line',
                        yMin: data.recommended_get_out,
                        yMax: data.recommended_get_out,
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        label: {
                            content: 'SELL ' + data.recommended_get_out.toFixed(2),
                            enabled: true,
                            backgroundColor: 'rgba(245, 158, 11, 0.8)',
                            color: 'white'
                        }
                    },
                    stopLoss: {
                        type: 'line',
                        yMin: data.recommended_stop_loss,
                        yMax: data.recommended_stop_loss,
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        label: {
                            content: 'STOP ' + data.recommended_stop_loss.toFixed(2),
                            enabled: true,
                            backgroundColor: 'rgba(239, 68, 68, 0.8)',
                            color: 'white'
                        }
                    }
                }
            };
            priceChart.update();
        }

    } catch (e) {
        console.error(e);
        clearMetrics();
    }
}

function clearMetrics() {
    document.getElementById('price-val').textContent = '$---.--';
    document.getElementById('get-in-val').textContent = '---';
    document.getElementById('get-out-val').textContent = '---';
    document.getElementById('stop-loss-val').textContent = '---';
    document.getElementById('gain-val').textContent = '---';
    document.getElementById('confidence-pct').textContent = '0%';
    document.getElementById('confidence-fill').style.width = '0%';
    document.getElementById('consensus-details').innerHTML = '';
    document.getElementById('last-trained').textContent = '---';
}

async function fetchHistoryAndDrawChart(ticker) {
    try {
        const resp = await fetch(`${API_BASE_URL}/api/history/${ticker}`);
        const history = await resp.json();
        if (history.error) return;

        const labels = history.map(h => h.Date.split(' ')[0]);
        const prices = history.map(h => h.Close);

        const ctx = document.getElementById('priceChart').getContext('2d');
        if (priceChart) priceChart.destroy();

        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Price',
                    data: prices,
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 0,
                            maxTicksLimit: 8
                        },
                        grid: { display: false }
                    },
                    y: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 15, 20, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                }
            }
        });
    } catch (e) { console.error(e); }
}

async function fetchSentiment(ticker) {
    const feed = document.getElementById('sentiment-feed');
    feed.innerHTML = '<div class="loading">Loading news...</div>';
    try {
        const resp = await fetch(`${API_BASE_URL}/api/sentiment/${ticker}`);
        const news = await resp.json();
        feed.innerHTML = '';
        if (news.length === 0) feed.innerHTML = '<div class="loading">No news found</div>';
        news.forEach(item => {
            const div = document.createElement('div');
            const sentClass = item.sentiment === 'positive' ? 'bullish' : (item.sentiment === 'negative' ? 'bearish' : 'neutral');
            const scorePct = Math.abs(item.sentiment_score * 100).toFixed(0);

            div.className = `news-item ${sentClass}`;
            div.innerHTML = `
                <div class="news-header">
                    <span class="sentiment-badge">${item.sentiment.toUpperCase()} ${scorePct}%</span>
                    <span class="meta">${item.publisher} • ${item.publish_time.split(' ')[0]}</span>
                </div>
                <span class="title">${item.title}</span>
            `;
            div.onclick = () => window.open(item.link, '_blank');
            feed.appendChild(div);
        });
    } catch (e) { feed.innerHTML = '<div class="loading">Error loading feed</div>'; }
}

function logConsole(text) {
    const out = document.getElementById('console-output');
    out.textContent += `\n[${new Date().toLocaleTimeString()}] ${text}`;
    out.scrollTop = out.scrollHeight;
}

function clearConsole() { document.getElementById('console-output').textContent = 'Workspace cleared.'; }

function toggleLoading(isLoading) {
    const btns = document.querySelectorAll('.btn-action');
    btns.forEach(b => b.disabled = isLoading);
}

// Loading state functions
function showLoading(message, progress) {
    const overlay = document.getElementById('loading-overlay');
    const messageEl = document.getElementById('loading-message');
    const progressEl = document.getElementById('progress-fill');

    overlay.classList.remove('hidden');
    messageEl.textContent = message;
    progressEl.style.width = progress + '%';
}

function updateLoadingProgress(message, progress) {
    document.getElementById('loading-message').textContent = message;
    document.getElementById('progress-fill').style.width = progress + '%';
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// Error handling functions
function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showErrorPanel(errorInfo) {
    const panel = document.createElement('div');
    panel.className = 'error-panel glass';
    panel.innerHTML = `
        <i class="fas fa-info-circle" style="font-size: 2rem; color: var(--accent-out);"></i>
        <h3>${errorInfo.title}</h3>
        <p>${errorInfo.message}</p>
        <p class="action-hint"><i class="fas fa-lightbulb"></i> ${errorInfo.action}</p>
    `;

    const mainBody = document.querySelector('.main-body');
    const existingError = mainBody.querySelector('.error-panel');
    if (existingError) existingError.remove();

    mainBody.insertBefore(panel, mainBody.querySelector('.cards-row'));
}

// Welcome modal functions
function closeWelcome() {
    const dontShow = document.getElementById('dont-show-again').checked;
    if (dontShow) {
        localStorage.setItem('welcomed', 'true');
    }
    document.getElementById('welcome-modal').classList.add('hidden');
}

function startWithSample() {
    closeWelcome();
    localStorage.setItem('welcomed', 'true');

    const select = document.getElementById('ticker-select');
    const aapl = [...select.options].find(opt => opt.value === 'AAPL');

    if (aapl) {
        select.value = 'AAPL';
        updateDashboard('AAPL');
        logConsole('👋 Welcome! Loaded Apple (AAPL) as a sample. Click "Predict" to see AI analysis.');
    } else {
        logConsole('👋 Welcome! Select a ticker from the dropdown to get started.');
    }
}

async function fetchModelMetrics(ticker) {
    const tbody = document.getElementById('model-table-body');
    const winnerEl = document.getElementById('winner-name');

    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="3" class="loading-cell">Loading metrics...</td></tr>';

    try {
        const resp = await fetch(`${API_BASE_URL}/api/model_metrics/${ticker}`);
        const data = await resp.json();

        if (data.error || !data.metrics) {
            tbody.innerHTML = '<tr><td colspan="3">No competition data found.</td></tr>';
            winnerEl.textContent = '---';
            return;
        }

        tbody.innerHTML = '';
        winnerEl.textContent = (data.winner || '---').toUpperCase();

        // Sort explicitly: Winner first, then by score
        const entries = Object.entries(data.metrics).sort((a, b) => {
            if (a[0] === data.winner) return -1;
            if (b[0] === data.winner) return 1;
            return b[1].direction_accuracy - a[1].direction_accuracy;
        });

        entries.forEach(([modelName, m]) => {
            const row = document.createElement('tr');
            if (modelName === data.winner) row.classList.add('winner-row');

            const acc = m.direction_accuracy ? m.direction_accuracy.toFixed(1) + '%' : 'N/A';
            const rmse = m.rmse ? m.rmse.toFixed(4) : 'N/A';

            row.innerHTML = `
                <td>${modelName.replace(/_/g, ' ').toUpperCase()}${modelName === data.winner ? ' [WINNER]' : ''}</td>
                <td>${acc}</td>
                <td>${rmse}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (e) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="3">Error loading metrics</td></tr>';
        console.error(e);
    }
}

function downloadReport() {
    window.print();
}

function openAnalytics() {
    const ticker = document.getElementById('ticker-select').value || 'AAPL';
    window.open(`/analytics/${ticker}`, '_blank');
}
