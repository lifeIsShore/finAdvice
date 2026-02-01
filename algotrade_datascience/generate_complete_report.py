"""
Generate Advanced Interactive HTML report with Ticker Filtering and Forecast Signals
"""

import json
import os
from pathlib import Path
from datetime import datetime
from config import DEFAULT_TICKERS


def generate_interactive_report(tickers=DEFAULT_TICKERS):
    """
    Generate an interactive HTML report with Ticker-specific views and forecast signals
    """
    
    # CSS for the forecast cards and animations
    forecast_styles = """
        .forecast-card {
            background: #fff;
            padding: 12px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            min-width: 250px;
            border-left: 5px solid var(--primary);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .forecast-card:hover {
            transform: scale(1.05);
        }

        .forecast-label {
            font-size: 0.7rem;
            font-weight: 800;
            color: #888;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }

        .forecast-main {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 5px;
        }

        .forecast-direction {
            font-size: 1.4rem;
            font-weight: 900;
        }

        .forecast-price {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--dark);
        }

        .forecast-details {
            font-size: 0.85rem;
            color: #666;
            font-weight: 500;
        }

        .forecast-meta {
            font-size: 0.7rem;
            color: #aaa;
            margin-top: 5px;
        }

        .signal-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 900;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
    """
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AlgoTrade ML - Advanced Multi-Asset Report</title>
    <style>
        :root {{
            --primary: #667eea;
            --secondary: #764ba2;
            --dark: #2c3e50;
            --light: #f8f9fa;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #ef5350;
            --glass: rgba(255, 255, 255, 0.9);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f0f2f5;
            padding: 0;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}
        
        header p {{
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
        }}

        .ticker-bar {{
            background: white;
            padding: 20px 40px;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            border-bottom: 2px solid #eee;
        }}

        .ticker-chip {{
            padding: 8px 16px;
            background: #eee;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 2px solid transparent;
            user-select: none;
        }}

        .ticker-chip:hover {{
            background: #e2e2e2;
            transform: translateY(-1px);
        }}

        .ticker-chip.active {{
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
            border-color: rgba(255,255,255,0.2);
        }}

        .ticker-chip.crypto {{
            border-left: 4px solid var(--warning);
        }}

        .main-content {{
            padding: 40px;
            flex-grow: 1;
        }}

        .ticker-card {{
            display: none;
            animation: fadeIn 0.4s ease-out;
        }}

        .ticker-card.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .card-header {{
            display: flex;
            align-items: baseline;
            gap: 15px;
            margin-bottom: 30px;
        }}

        .card-header h2 {{
            font-size: 2.5rem;
            color: var(--dark);
        }}

        .status-pill {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}

        .stat-box {{
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            border: 1px solid #f1f1f1;
        }}

        .stat-label {{
            font-size: 0.85rem;
            color: #777;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            color: var(--dark);
        }}

        .chart-box {{
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }}

        .chart-box h3 {{
            margin-bottom: 20px;
            color: var(--primary);
            font-size: 1.4rem;
        }}

        .img-container {{
            width: 100%;
            overflow: hidden;
            border-radius: 12px;
        }}

        .img-container img {{
            width: 100%;
            display: block;
            transition: transform 0.3s;
        }}

        .img-container img:hover {{
            transform: scale(1.02);
        }}

        .metrics-table-container {{
            overflow-x: auto;
            margin-top: 20px;
            margin-bottom: 30px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            text-align: left;
            padding: 15px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9rem;
            font-weight: 700;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            font-size: 0.95rem;
        }}

        .best-row {{
            background: rgba(40, 167, 69, 0.05);
        }}

        .accent-text {{
            color: var(--primary);
            font-weight: 700;
        }}

        .section h2 {{
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8rem;
            border-bottom: 3px solid var(--primary);
            display: inline-block;
            padding-bottom: 5px;
        }}

        .no-data {{
            text-align: center;
            padding: 100px;
            background: white;
            border-radius: 20px;
            color: #999;
        }}

        footer {{
            background: var(--dark);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .footer-logo {{
            font-weight: 800;
            font-size: 1.5rem;
            margin-bottom: 10px;
            display: block;
        }}
        
        {forecast_styles}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AlgoTrade ML</h1>
            <p>Intelligence-Driven Market Forecasting & Visual Analytics</p>
        </header>
        
        <div class="ticker-bar" id="tickerSelector">
            {generate_ticker_bar(tickers)}
        </div>

        <div class="main-content" id="reportContent">
            {generate_ticker_cards(tickers)}
        </div>

        <footer>
            <span class="footer-logo">AlgoTrade DataScience</span>
            <p>Forecasts generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>

    <script>
        function selectTicker(tickerId) {{
            // Update chips
            document.querySelectorAll('.ticker-chip').forEach(chip => {{
                chip.classList.remove('active');
            }});
            const activeChip = Array.from(document.querySelectorAll('.ticker-chip')).find(c => c.textContent === tickerId);
            if (activeChip) activeChip.classList.add('active');

            // Update cards
            document.querySelectorAll('.ticker-card').forEach(card => {{
                card.classList.remove('active');
            }});
            const activeCard = document.getElementById('card-' + tickerId);
            if (activeCard) activeCard.classList.add('active');
            
            // Re-hash for sharing
            window.location.hash = tickerId;
        }}

        // Initialization
        window.addEventListener('DOMContentLoaded', () => {{
            const hash = window.location.hash.substring(1);
            if (hash) {{
                selectTicker(hash);
            }} else {{
                // Select first available chip
                const first = document.querySelector('.ticker-chip');
                if (first) selectTicker(first.textContent);
            }}
        }});
    </script>
</body>
</html>
"""
    
    output_path = Path('data/complete_ml_report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_path


def generate_ticker_bar(tickers):
    items = []
    for t in tickers:
        is_crypto = "-USD" in t
        cls = "ticker-chip" + (" crypto" if is_crypto else "")
        items.append(f'<div class="{cls}" onclick="selectTicker(\'{t}\')">{t}</div>')
    return "\n".join(items)


def generate_ticker_cards(tickers):
    cards = []
    for t in tickers:
        cards.append(generate_one_ticker_card(t))
    return "\n".join(cards)


def generate_one_ticker_card(ticker):
    # Try to load metric data
    data_file = Path(f'data/baseline_models_{ticker}.json')
    metrics_block = ""
    summary_boxes = ""
    interval_data = {}
    
    if data_file.exists():
        with open(data_file, 'r') as f:
            stats = json.load(f)
        
        # Extract some highlights
        all_r2 = []
        for interval in stats.values():
            for model in interval['metrics'].values():
                if model['r2'] is not None:
                    all_r2.append(model['r2'])
        
        best_r2 = max(all_r2) if all_r2 else 0
        
        summary_boxes = f"""
        <div class="grid">
            <div class="stat-box">
                <div class="stat-label">Max Predictive R²</div>
                <div class="stat-value">{(best_r2*100):.1f}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Active Forecasts</div>
                <div class="stat-value">{len(stats)} Intervals</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Asset Classification</div>
                <div class="stat-value">{'Cryptocurrency' if '-USD' in ticker else 'Equity Stock'}</div>
            </div>
        </div>
        """
        
        # Build tables and store forecast for each interval
        for interval, content in stats.items():
            # Extract next prediction
            pred = content.get('next_prediction')
            forecast_html = ""
            if pred:
                color = "var(--success)" if pred['direction'] == "UP" else "var(--danger)"
                icon = "▲" if pred['direction'] == "UP" else "▼"
                forecast_html = f"""
                <div class="forecast-card" style="border-left: 5px solid {color}">
                    <div class="forecast-label">NEXT {interval.upper()} SIGNAL</div>
                    <div class="forecast-main">
                        <span class="forecast-direction" style="color: {color}">{icon} {pred['direction']}</span>
                        <span class="forecast-price">${pred['predicted_next']:.2f}</span>
                    </div>
                    <div class="forecast-details">
                        Current: ${pred['current_close']:.2f} | 
                        Change: <span style="color: {color}">{pred['pct_change']:+.2f}%</span>
                    </div>
                    <div class="forecast-meta">via {pred['model_used']}</div>
                </div>
                """
            
            interval_data[interval] = {
                'forecast': forecast_html,
                'img': f"visualizations/{ticker}/candlestick_{interval}.png"
            }

            metrics_block += f"<h3>{interval.upper()} Model Quality</h3>"
            metrics_block += """
            <div class="metrics-table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>RMSE</th>
                            <th>R² Score</th>
                            <th>Error (MAPE)</th>
                            <th>Direction Acc.</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Sort models by R2
            models = sorted(content['metrics'].values(), key=lambda x: (x['r2'] if x['r2'] is not None else -999), reverse=True)
            for i, m in enumerate(models):
                row_cls = "best-row" if i == 0 else ""
                r2 = f"{(m['r2']*100):.1f}%" if m['r2'] is not None else "N/A"
                acc = f"{m['direction_accuracy']:.1f}%" if m['direction_accuracy'] is not None else "N/A"
                metrics_block += f"""
                    <tr class="{row_cls}">
                        <td>{m['model']}</td>
                        <td>{m['rmse']:.4f}</td>
                        <td class="accent-text">{r2}</td>
                        <td>{m['mape']:.2f}%</td>
                        <td>{acc}</td>
                    </tr>
                """
            metrics_block += "</tbody></table></div>"
    else:
        summary_boxes = f"""
        <div class="no-data">
            <h2>Data Acquisition & Modeling Pending</h2>
            <p>Run the analysis pipeline to generate forecasts for {ticker}</p>
        </div>
        """

    def get_chart_block(interval, title):
        data = interval_data.get(interval, {})
        forecast = data.get('forecast', "")
        img = data.get('img', f"visualizations/{ticker}/candlestick_{interval}.png")
        
        return f"""
        <div class="chart-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                <h3>{title}</h3>
                {forecast}
            </div>
            <div class="img-container">
                <img src="{img}" onerror="this.src='https://placehold.co/1200x600?text=Chart+Pending'" />
            </div>
        </div>
        """

    charts_block = f"""
    <div class="section">
        <h2>Visual Market Forecasts</h2>
        {get_chart_block('1d', 'Daily (1D) Projection')}
        
        <div class="grid">
            {get_chart_block('4h', '4-Hour (4H) Intraday')}
            {get_chart_block('1h', '1-Hour (1H) Scalp')}
        </div>
    </div>

    <div class="section">
        <h2>Performance Deep-Dive</h2>
        <div class="grid">
            <div class="chart-box">
                <h3>R² Comparison Across Models</h3>
                <div class="img-container">
                    <img src="visualizations/{ticker}/r2_comparison.png" onerror="this.style.display='none'"/>
                </div>
            </div>
            <div class="chart-box">
                <h3>Directional Hit Rate</h3>
                <div class="img-container">
                    <img src="visualizations/{ticker}/direction_accuracy.png" onerror="this.style.display='none'"/>
                </div>
            </div>
        </div>
        <div class="chart-box">
            <h3>Metric Correlation Heatmap</h3>
            <div class="img-container">
                <img src="visualizations/{ticker}/metrics_heatmap.png" onerror="this.style.display='none'"/>
            </div>
        </div>
    </div>
    """

    return f"""
    <div class="ticker-card" id="card-{ticker}">
        <div class="card-header">
            <h2>{ticker}</h2>
            <span class="status-pill" style="background: #e3f2fd; color: #1565c0;">ML Analysis Active</span>
        </div>
        
        {summary_boxes}
        
        <div class="section">
            <h2>Predictive Analysis</h2>
            {metrics_block}
        </div>
 
        {charts_block if data_file.exists() else ""}
    </div>
    """


if __name__ == "__main__":
    path = generate_interactive_report()
    print(f"SUCCESS: Success: Interactive report updated with forecast signals at: {path}")
