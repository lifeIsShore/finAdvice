let priceChart = null;

// Dynamic API Base Detection
const getApiBaseUrl = () => {
    // If we're running on the Flask server, use the current origin
    if (window.location.protocol !== 'file:') {
        return window.location.origin;
    }
    // If we're opening as a local file, default to the local Flask server
    return 'http://127.0.0.1:5000';
};

const API_BASE_URL = getApiBaseUrl();

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
        action: 'Check if the Flask server is running on ' + API_BASE_URL
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
        const customField = document.getElementById('custom-ticker');
        const custom = customField ? customField.value.trim().toUpperCase() : '';
        return custom || tickerSelect.value;
    };

    if (tickerSelect) {
        tickerSelect.addEventListener('change', () => {
            const customField = document.getElementById('custom-ticker');
            if (customField) customField.value = ''; // Clear custom if dropdown used
            updateDashboard(tickerSelect.value);
        });
    }

    // Add event listener for custom ticker input
    const customTickerInput = document.getElementById('custom-ticker');
    if (customTickerInput) {
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
    }

    if (runPipelineBtn) {
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
                logConsole("[OK] Data fetched successfully");

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
                logConsole("[OK] ML predictions complete");
                logConsole(mlData.output);

                // Step 3: Refresh
                updateLoadingProgress("Loading results...", 100);
                setTimeout(() => {
                    hideLoading();
                    if (window.location.protocol === 'file:') {
                        window.location.href = `index.html?ticker=${ticker}`;
                    } else {
                        window.location.href = `/?ticker=${ticker}`;
                    }
                }, 500);

            } catch (e) {
                hideLoading();
                logConsole(`Error: ${e.message}`);
                showError("Failed to complete analysis. Please try again.");
            }
        });
    }

    if (runMLBtn) {
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
    }
});

async function loadTickers(targetTicker) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickers`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const tickers = await response.json();

        if (tickers.error) throw new Error(tickers.error);

        const select = document.getElementById('ticker-select');
        if (!select) return;

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

    // Sync elements
    const select = document.getElementById('ticker-select');
    const customInput = document.getElementById('custom-ticker');

    if (select && select.value !== ticker && [...select.options].some(o => o.value === ticker)) {
        select.value = ticker;
        if (customInput) customInput.value = '';
    } else if (customInput && (!select || select.value !== ticker)) {
        customInput.value = ticker;
    }

    const tickerDisplay = document.getElementById('current-ticker');
    if (tickerDisplay) tickerDisplay.textContent = ticker;

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

        // UI Updates
        const priceVal = document.getElementById('price-val');
        if (priceVal) priceVal.textContent = `$${data.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        const getInVal = document.getElementById('get-in-val');
        if (getInVal) getInVal.textContent = `$${data.recommended_get_in.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        const getOutVal = document.getElementById('get-out-val');
        if (getOutVal) getOutVal.textContent = `$${data.recommended_get_out.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        const stopLossVal = document.getElementById('stop-loss-val');
        if (stopLossVal) stopLossVal.textContent = `$${data.recommended_stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        const gainVal = document.getElementById('gain-val');
        if (gainVal) gainVal.textContent = `${data.potential_gain.toFixed(2)}%`;

        const badge = document.getElementById('ticker-badge');
        if (badge) {
            badge.textContent = data.asset_type || 'STOCK';
            badge.style.color = data.asset_type === 'Crypto' ? 'var(--secondary)' : 'var(--primary)';
        }

        // Confidence
        const confidence = data.confidence_score !== undefined ? data.confidence_score : 0;
        const fill = document.getElementById('confidence-fill');
        const pct = document.getElementById('confidence-pct');
        if (fill) fill.style.width = `${confidence}%`;
        if (pct) pct.textContent = `${Math.round(confidence)}%`;

        if (confidence === 0) {
            logConsole(`[WARNING] Confidence score is 0 for ${ticker}. This may indicate data issues.`);
        }

        // Consensus
        const list = document.getElementById('consensus-details');
        if (list) {
            list.innerHTML = '';
            const consensus = data.consensus || {};
            const timeframes = ['1h', '4h', '1d', '1wk', '1mo'];

            timeframes.forEach(interval => {
                const prediction = consensus[interval];
                if (!prediction) return;

                let direction = 'NEUTRAL';
                let changePercent = 0;
                let conf = data.confidence_score || 0;
                let bestModel = 'Ensemble';

                if (typeof prediction === 'string') {
                    direction = prediction;
                    changePercent = prediction === 'UP' ? 0.5 : -0.5;
                } else {
                    direction = prediction.sentiment || prediction.direction || 'NEUTRAL';
                    changePercent = prediction.change_percent || 0;
                    conf = prediction.confidence || conf;
                    bestModel = prediction.best_model || 'Ensemble';
                }

                let sentiment, emoji, color;
                if (changePercent > 2.0) { sentiment = 'Dramatic UP'; emoji = '+++'; color = '#27ae60'; }
                else if (changePercent > 1.0) { sentiment = 'Strong UP'; emoji = '++'; color = '#2ecc71'; }
                else if (changePercent > 0.2) { sentiment = 'Up'; emoji = '+'; color = '#3498db'; }
                else if (changePercent > -0.2) { sentiment = 'Neutral'; emoji = '='; color = '#95a5a6'; }
                else if (changePercent > -1.0) { sentiment = 'Down'; emoji = '-'; color = '#e74c3c'; }
                else if (changePercent > -2.0) { sentiment = 'Strong DOWN'; emoji = '--'; color = '#c0392b'; }
                else { sentiment = 'Dramatic DOWN'; emoji = '---'; color = '#8b0000'; }

                const row = document.createElement('div');
                row.className = 'metric-row consensus-row';
                row.style.borderLeft = `4px solid ${color}`;
                row.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                        <span style="font-weight: 600; min-width: 35px; color: #a0aec0;">${interval.toUpperCase()}</span>
                        <span style="color: ${color}; font-weight: 600; font-size: 1.1rem;">${emoji}</span>
                        <span style="color: ${color}; font-weight: 500;">${sentiment}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; text-align: right;">
                        <span style="color: ${color}; font-weight: 600;">${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%</span>
                        <span style="color: #a0aec0; font-size: 0.8rem;">${Math.round(conf)}% • ${bestModel}</span>
                    </div>
                `;
                list.appendChild(row);
            });
        }

        const lastTrained = document.getElementById('last-trained');
        if (lastTrained) lastTrained.textContent = data.last_trained || '---';

        const winnerName = document.getElementById('winner-name');
        if (winnerName && data.model_competition && data.model_competition.winner) {
            winnerName.textContent = data.model_competition.winner.toUpperCase();
        }

        // Market Sentiment
        const sentimentBox = document.getElementById('market-sentiment-box');
        if (sentimentBox && data.market_sentiment_label) {
            const sentimentIcon = document.getElementById('sentiment-icon');
            const sentimentLabel = document.getElementById('sentiment-label');
            const sentimentValue = document.getElementById('sentiment-value');

            sentimentBox.style.display = 'flex';
            const iconMap = { '[DRAMATICALLY_UP]': '+++', '[UP]': '++', '[SIDEWAYS]': '=', '[DOWN]': '--', '[DRAMATICALLY_DOWN]': '---' };
            if (sentimentIcon) sentimentIcon.textContent = iconMap[data.market_sentiment_icon] || data.market_sentiment_icon || '=';
            if (sentimentLabel) sentimentLabel.textContent = 'Market Outlook';
            if (sentimentValue) {
                sentimentValue.textContent = data.market_sentiment_label;
                sentimentValue.classList.remove('dramatically-up', 'up', 'sideways', 'down', 'dramatically-down');
                sentimentValue.classList.add(data.market_sentiment_label.toLowerCase().replace(' ', '-'));
            }
        }

        // Annotations
        if (priceChart) {
            priceChart.options.plugins.annotation = {
                annotations: {
                    getIn: { type: 'line', yMin: data.recommended_get_in, yMax: data.recommended_get_in, borderColor: '#10b981', borderWidth: 2, label: { content: 'BUY', enabled: true, backgroundColor: 'rgba(16, 185, 129, 0.8)' } },
                    getOut: { type: 'line', yMin: data.recommended_get_out, yMax: data.recommended_get_out, borderColor: '#f59e0b', borderWidth: 2, label: { content: 'SELL', enabled: true, backgroundColor: 'rgba(245, 158, 11, 0.8)' } },
                    stopLoss: { type: 'line', yMin: data.recommended_stop_loss, yMax: data.recommended_stop_loss, borderColor: '#ef4444', borderWidth: 2, label: { content: 'STOP', enabled: true, backgroundColor: 'rgba(239, 68, 68, 0.8)' } }
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
    ['price-val', 'get-in-val', 'get-out-val', 'stop-loss-val', 'gain-val', 'last-trained'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '---';
    });
    const pct = document.getElementById('confidence-pct');
    if (pct) pct.textContent = '0%';
    const fill = document.getElementById('confidence-fill');
    if (fill) fill.style.width = '0%';
    const details = document.getElementById('consensus-details');
    if (details) details.innerHTML = '';
}

async function fetchHistoryAndDrawChart(ticker) {
    try {
        const resp = await fetch(`${API_BASE_URL}/api/history/${ticker}`);
        const history = await resp.json();
        if (history.error) return;

        const labels = history.map(h => h.Date.split(' ')[0]);
        const prices = history.map(h => h.Close);

        const canvas = document.getElementById('priceChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (priceChart) priceChart.destroy();

        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{ label: 'Price', data: prices, borderColor: '#6366f1', borderWidth: 2, pointRadius: 0, fill: true, backgroundColor: 'rgba(99, 102, 241, 0.1)', tension: 0.4 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8', maxTicksLimit: 8 }, grid: { display: false } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    } catch (e) { console.error(e); }
}

async function fetchSentiment(ticker) {
    const feed = document.getElementById('sentiment-feed');
    if (!feed) return;
    feed.innerHTML = '<div class="loading">Loading news...</div>';
    try {
        const resp = await fetch(`${API_BASE_URL}/api/sentiment/${ticker}`);
        const news = await resp.json();
        feed.innerHTML = '';
        if (news.length === 0) feed.innerHTML = '<div class="loading">No news found</div>';
        news.forEach(item => {
            const div = document.createElement('div');
            const sentClass = item.sentiment === 'positive' ? 'bullish' : (item.sentiment === 'negative' ? 'bearish' : 'neutral');
            div.className = `news-item ${sentClass}`;
            div.innerHTML = `
                <div class="news-header">
                    <span class="sentiment-badge">${item.sentiment.toUpperCase()}</span>
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
    if (out) {
        out.textContent += `\n[${new Date().toLocaleTimeString()}] ${text}`;
        out.scrollTop = out.scrollHeight;
    }
}

function clearConsole() {
    const out = document.getElementById('console-output');
    if (out) out.textContent = 'Workspace cleared.';
}

function showLoading(message, progress) {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    document.getElementById('loading-message').textContent = message;
    document.getElementById('progress-fill').style.width = progress + '%';
}

function updateLoadingProgress(message, progress) {
    const msg = document.getElementById('loading-message');
    const fill = document.getElementById('progress-fill');
    if (msg) msg.textContent = message;
    if (fill) fill.style.width = progress + '%';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 4000);
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
    if (mainBody) {
        const existingError = mainBody.querySelector('.error-panel');
        if (existingError) existingError.remove();
        mainBody.insertBefore(panel, mainBody.querySelector('.cards-row'));
    }
}

function closeWelcome() {
    const check = document.getElementById('dont-show-again');
    if (check && check.checked) localStorage.setItem('welcomed', 'true');
    const modal = document.getElementById('welcome-modal');
    if (modal) modal.classList.add('hidden');
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
            if (winnerEl) winnerEl.textContent = '---';
            return;
        }
        tbody.innerHTML = '';
        if (winnerEl) winnerEl.textContent = (data.winner || '---').toUpperCase();
        const entries = Object.entries(data.metrics).sort((a, b) => {
            if (a[0] === data.winner) return -1;
            if (b[0] === data.winner) return 1;
            return (b[1].direction_accuracy || 0) - (a[1].direction_accuracy || 0);
        });
        entries.forEach(([modelName, m]) => {
            const row = document.createElement('tr');
            if (modelName === data.winner) row.classList.add('winner-row');
            row.innerHTML = `
                <td>${modelName.replace(/_/g, ' ').toUpperCase()}${modelName === data.winner ? ' [WINNER]' : ''}</td>
                <td>${m.direction_accuracy ? m.direction_accuracy.toFixed(1) + '%' : 'N/A'}</td>
                <td>${m.rmse ? m.rmse.toFixed(4) : 'N/A'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="3">Error loading metrics</td></tr>';
    }
}

function downloadReport() { window.print(); }

function openAnalytics() {
    const ticker = document.getElementById('ticker-select').value || 'AAPL';
    // Use analytics.html?ticker=... as it works for both Flask root and file://
    window.open(`analytics.html?ticker=${ticker}`, '_blank');
}
