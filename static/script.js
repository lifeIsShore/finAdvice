let priceChart = null;

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
            const resp = await fetch('/api/run_pipeline', {
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

            const mlResp = await fetch('/api/run_ml', {
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
                window.location.href = `/?ticker=${ticker}`;
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
            const resp = await fetch('/api/run_ml', {
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
        const response = await fetch('/api/tickers');
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
    fetchHistoryAndDrawChart(ticker);

    try {
        const response = await fetch(`/api/results/${ticker}`);
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
        document.getElementById('price-val').textContent = `$${data.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('get-in-val').textContent = `$${data.recommended_get_in.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('get-out-val').textContent = `$${data.recommended_get_out.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('stop-loss-val').textContent = `$${data.recommended_stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('gain-val').textContent = `${data.potential_gain.toFixed(2)}%`;

        const badge = document.getElementById('asset-type');
        badge.textContent = data.asset_type;
        badge.style.color = data.asset_type === 'Crypto' ? 'var(--secondary)' : 'var(--primary)';

        // Confidence
        const confidence = data.confidence_score;
        document.getElementById('confidence-fill').style.width = `${confidence}%`;
        document.getElementById('confidence-pct').textContent = `${Math.round(confidence)}%`;

        // Consensus
        const list = document.getElementById('consensus-details');
        list.innerHTML = '';
        const consensus = data.consensus || {};
        for (const [interval, trend] of Object.entries(consensus)) {
            const row = document.createElement('div');
            row.className = 'metric-row';
            row.innerHTML = `<span>${interval} Trend</span><span style="color: ${trend === 'UP' ? 'var(--accent-in)' : 'var(--accent-risk)'}">${trend}</span>`;
            list.appendChild(row);
        }



        // Add predictions to chart if it exists
        if (priceChart) {
            priceChart.options.plugins.annotation = {
                annotations: {
                    getIn: { type: 'line', yMin: data.recommended_get_in, yMax: data.recommended_get_in, borderColor: '#10b981', borderWidth: 2, borderDash: [5, 5], label: { content: 'BUY', enabled: true } },
                    getOut: { type: 'line', yMin: data.recommended_get_out, yMax: data.recommended_get_out, borderColor: '#f59e0b', borderWidth: 2, borderDash: [5, 5], label: { content: 'SELL', enabled: true } }
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
        const resp = await fetch(`/api/history/${ticker}`);
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
                scales: {
                    x: { ticks: { color: '#94a3b8', maxRotation: 0 }, grid: { display: false } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    } catch (e) { console.error(e); }
}

async function fetchSentiment(ticker) {
    const feed = document.getElementById('sentiment-feed');
    feed.innerHTML = '<div class="loading">Loading news...</div>';
    try {
        const resp = await fetch(`/api/sentiment/${ticker}`);
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
