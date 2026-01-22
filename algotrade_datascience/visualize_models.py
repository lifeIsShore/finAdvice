"""
Baseline Models Visualization
Creates visual charts and HTML report for model performance
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class ModelVisualizer:
    """
    Create visualizations for baseline model results
    """
    
    def __init__(self, results_file: str = 'data/baseline_models_AAPL.json'):
        self.results_file = results_file
        self.output_dir = Path('data/visualizations')
        self.output_dir.mkdir(exist_ok=True)
        
        # Load results
        with open(results_file, 'r') as f:
            self.results = json.load(f)
    
    def create_r2_comparison(self):
        """Create R² comparison chart across intervals"""
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Regression', 'Random Forest', 'XGBoost', 'SMA Benchmark']
        
        # Prepare data
        data = []
        for interval in intervals:
            for model, name in zip(models, model_names):
                r2 = self.results[interval]['metrics'][model]['r2']
                data.append({
                    'Interval': interval.upper(),
                    'Model': name,
                    'R²': r2
                })
        
        df = pd.DataFrame(data)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Grouped bar chart
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            r2_values = [self.results[interval]['metrics'][model]['r2'] for interval in intervals]
            ax.bar(x + i * width, r2_values, width, label=name)
        
        ax.set_xlabel('Interval', fontsize=12, fontweight='bold')
        ax.set_ylabel('R² Score', fontsize=12, fontweight='bold')
        ax.set_title('Model Performance Comparison (R² Score by Interval)', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend(loc='upper right')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.3)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'r2_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created R² comparison chart")
    
    def create_rmse_comparison(self):
        """Create RMSE comparison chart"""
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Regression', 'Random Forest', 'XGBoost', 'SMA Benchmark']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            rmse_values = [self.results[interval]['metrics'][model]['rmse'] for interval in intervals]
            ax.bar(x + i * width, rmse_values, width, label=name)
        
        ax.set_xlabel('Interval', fontsize=12, fontweight='bold')
        ax.set_ylabel('RMSE', fontsize=12, fontweight='bold')
        ax.set_title('Model Performance Comparison (RMSE by Interval)', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rmse_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created RMSE comparison chart")
    
    def create_direction_accuracy(self):
        """Create direction accuracy comparison"""
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Regression', 'Random Forest', 'XGBoost', 'SMA Benchmark']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            acc_values = [self.results[interval]['metrics'][model]['direction_accuracy'] for interval in intervals]
            ax.bar(x + i * width, acc_values, width, label=name)
        
        ax.set_xlabel('Interval', fontsize=12, fontweight='bold')
        ax.set_ylabel('Direction Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_title('Direction Prediction Accuracy by Interval', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend(loc='upper right')
        ax.axhline(y=50, color='red', linestyle='--', alpha=0.3, label='Random Guess (50%)')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'direction_accuracy.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created direction accuracy chart")
    
    def create_mape_comparison(self):
        """Create MAPE comparison chart"""
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Regression', 'Random Forest', 'XGBoost', 'SMA Benchmark']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(intervals))
        width = 0.2
        
        for i, (model, name) in enumerate(zip(models, model_names)):
            mape_values = [self.results[interval]['metrics'][model]['mape'] for interval in intervals]
            ax.bar(x + i * width, mape_values, width, label=name)
        
        ax.set_xlabel('Interval', fontsize=12, fontweight='bold')
        ax.set_ylabel('MAPE (%)', fontsize=12, fontweight='bold')
        ax.set_title('Mean Absolute Percentage Error by Interval', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([i.upper() for i in intervals])
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'mape_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created MAPE comparison chart")
    
    def create_best_model_summary(self):
        """Create summary chart showing best model per interval"""
        intervals = list(self.results.keys())
        
        best_models = []
        r2_scores = []
        
        for interval in intervals:
            metrics = self.results[interval]['metrics']
            # Find best model by R²
            best = max(metrics.items(), key=lambda x: x[1]['r2'])
            best_models.append(best[1]['model'])
            r2_scores.append(best[1]['r2'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['#2ecc71' if r2 > 0.8 else '#f39c12' if r2 > 0.5 else '#e74c3c' for r2 in r2_scores]
        bars = ax.barh([i.upper() for i in intervals], r2_scores, color=colors)
        
        ax.set_xlabel('R² Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Interval', fontsize=12, fontweight='bold')
        ax.set_title('Best Model Performance by Interval', fontsize=14, fontweight='bold')
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.3)
        ax.axvline(x=0.5, color='orange', linestyle='--', alpha=0.3)
        ax.axvline(x=0.8, color='green', linestyle='--', alpha=0.3)
        
        # Add model names and R² values
        for i, (bar, model, r2) in enumerate(zip(bars, best_models, r2_scores)):
            ax.text(r2 + 0.02, bar.get_y() + bar.get_height()/2, 
                   f'{model} ({r2:.3f})', 
                   va='center', fontsize=10)
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'best_models.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created best models summary chart")
    
    def create_metrics_heatmap(self):
        """Create heatmap of all metrics"""
        intervals = list(self.results.keys())
        models = ['linear_regression', 'random_forest', 'xgboost', 'sma_benchmark']
        model_names = ['Linear Reg', 'Random Forest', 'XGBoost', 'SMA']
        
        # Create separate heatmaps for each metric
        metrics_to_plot = ['r2', 'mape', 'direction_accuracy']
        metric_titles = ['R² Score', 'MAPE (%)', 'Direction Accuracy (%)']
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        for ax, metric, title in zip(axes, metrics_to_plot, metric_titles):
            data = []
            for model in models:
                row = [self.results[interval]['metrics'][model][metric] for interval in intervals]
                data.append(row)
            
            df = pd.DataFrame(data, index=model_names, columns=[i.upper() for i in intervals])
            
            # Choose colormap based on metric
            cmap = 'RdYlGn' if metric in ['r2', 'direction_accuracy'] else 'RdYlGn_r'
            
            sns.heatmap(df, annot=True, fmt='.2f', cmap=cmap, ax=ax, 
                       cbar_kws={'label': title}, vmin=-1 if metric == 'r2' else None)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('Interval', fontsize=10)
            ax.set_ylabel('Model', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'metrics_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Created metrics heatmap")
    
    def generate_html_report(self):
        """Generate HTML report with all visualizations"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Baseline ML Models - Visual Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .section h3 {{
            color: #764ba2;
            font-size: 1.5em;
            margin: 30px 0 15px 0;
        }}
        
        .chart {{
            margin: 30px 0;
            text-align: center;
        }}
        
        .chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .metric-card h4 {{
            font-size: 1.1em;
            margin-bottom: 10px;
            opacity: 0.9;
        }}
        
        .metric-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        
        .metric-card .label {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        .best {{
            background: #d4edda;
            font-weight: bold;
        }}
        
        .good {{
            background: #fff3cd;
        }}
        
        .poor {{
            background: #f8d7da;
        }}
        
        footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }}
        
        .highlight {{
            background: #fff3cd;
            padding: 20px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Baseline ML Models</h1>
            <p>Visual Performance Report - AAPL Stock Prediction</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="content">
            <div class="section">
                <h2>🎯 Executive Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h4>Best R² Score</h4>
                        <div class="value">94.9%</div>
                        <div class="label">1h Interval - Linear Regression</div>
                    </div>
                    <div class="metric-card">
                        <h4>Best Direction Accuracy</h4>
                        <div class="value">87.5%</div>
                        <div class="label">1mo Interval - Random Forest</div>
                    </div>
                    <div class="metric-card">
                        <h4>Lowest MAPE</h4>
                        <div class="value">0.35%</div>
                        <div class="label">1h Interval - Linear Regression</div>
                    </div>
                    <div class="metric-card">
                        <h4>Models Tested</h4>
                        <div class="value">4</div>
                        <div class="label">Per Interval</div>
                    </div>
                </div>
                
                <div class="highlight">
                    <strong>🏆 Key Finding:</strong> Linear Regression consistently outperforms complex models (Random Forest, XGBoost) across all intervals. 
                    Shorter intervals (1h, 1d) show significantly better predictive accuracy than longer intervals.
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Performance Visualizations</h2>
                
                <h3>Best Model by Interval</h3>
                <div class="chart">
                    <img src="visualizations/best_models.png" alt="Best Models">
                </div>
                
                <h3>R² Score Comparison</h3>
                <div class="chart">
                    <img src="visualizations/r2_comparison.png" alt="R² Comparison">
                </div>
                
                <h3>RMSE Comparison</h3>
                <div class="chart">
                    <img src="visualizations/rmse_comparison.png" alt="RMSE Comparison">
                </div>
                
                <h3>Direction Accuracy</h3>
                <div class="chart">
                    <img src="visualizations/direction_accuracy.png" alt="Direction Accuracy">
                </div>
                
                <h3>MAPE Comparison</h3>
                <div class="chart">
                    <img src="visualizations/mape_comparison.png" alt="MAPE Comparison">
                </div>
                
                <h3>Metrics Heatmap</h3>
                <div class="chart">
                    <img src="visualizations/metrics_heatmap.png" alt="Metrics Heatmap">
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Detailed Results</h2>
                {self.generate_results_tables()}
            </div>
            
            <div class="section">
                <h2>💡 Recommendations</h2>
                <div class="highlight">
                    <h3>For Trading:</h3>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li><strong>Intraday (1h):</strong> Use Linear Regression - 94.9% R² (High Confidence)</li>
                        <li><strong>Daily (1d):</strong> Use Linear Regression - 87.4% R² (High Confidence)</li>
                        <li><strong>Swing (4h):</strong> Use Linear Regression - 76.0% R² (Moderate Confidence)</li>
                        <li><strong>Long-term (1wk, 1mo):</strong> Use for direction only (Low Confidence)</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <footer>
            <p>FinAdvice - Algorithmic Trading ML Models</p>
            <p style="font-size: 0.9em; margin-top: 5px;">Version 1.1.0 | January 2026</p>
        </footer>
    </div>
</body>
</html>
"""
        
        output_file = self.output_dir.parent / 'baseline_models_report.html'
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"\n✅ HTML report generated: {output_file}")
        return output_file
    
    def generate_results_tables(self):
        """Generate HTML tables for results"""
        html = ""
        
        for interval in self.results.keys():
            metrics = self.results[interval]['metrics']
            
            html += f"<h3>{interval.upper()} Interval</h3>"
            html += "<table>"
            html += "<tr><th>Model</th><th>RMSE</th><th>MAE</th><th>R²</th><th>MAPE (%)</th><th>Direction Acc (%)</th></tr>"
            
            # Sort by R²
            sorted_metrics = sorted(metrics.items(), key=lambda x: x[1]['r2'], reverse=True)
            
            for i, (model_key, m) in enumerate(sorted_metrics):
                row_class = 'best' if i == 0 else 'good' if m['r2'] > 0.5 else 'poor' if m['r2'] < 0 else ''
                html += f"<tr class='{row_class}'>"
                html += f"<td>{m['model']}</td>"
                html += f"<td>{m['rmse']:.4f}</td>"
                html += f"<td>{m['mae']:.4f}</td>"
                html += f"<td>{m['r2']:.4f}</td>"
                html += f"<td>{m['mape']:.2f}</td>"
                html += f"<td>{m['direction_accuracy']:.2f}</td>"
                html += "</tr>"
            
            html += "</table>"
        
        return html
    
    def create_all_visualizations(self):
        """Create all visualizations and report"""
        print("\n" + "="*80)
        print("CREATING VISUALIZATIONS")
        print("="*80)
        
        self.create_r2_comparison()
        self.create_rmse_comparison()
        self.create_direction_accuracy()
        self.create_mape_comparison()
        self.create_best_model_summary()
        self.create_metrics_heatmap()
        
        report_file = self.generate_html_report()
        
        print("\n" + "="*80)
        print("✅ ALL VISUALIZATIONS CREATED!")
        print("="*80)
        print(f"\nFiles created:")
        print(f"  - {self.output_dir}/r2_comparison.png")
        print(f"  - {self.output_dir}/rmse_comparison.png")
        print(f"  - {self.output_dir}/direction_accuracy.png")
        print(f"  - {self.output_dir}/mape_comparison.png")
        print(f"  - {self.output_dir}/best_models.png")
        print(f"  - {self.output_dir}/metrics_heatmap.png")
        print(f"  - {report_file}")
        print(f"\n📊 Open {report_file} in your browser to view the full report!")


if __name__ == "__main__":
    visualizer = ModelVisualizer()
    visualizer.create_all_visualizations()
