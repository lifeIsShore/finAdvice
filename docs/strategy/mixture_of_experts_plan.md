# Technical Strategy: Conditional Mixture of Experts (MoE)
**Architectural Specification for Alpha-Seeking ML Pipeline**

## 1. Executive Summary
This document outlines the transition from a **Competitive Consensus** model to a **Conditional Mixture of Experts (MoE)** architecture. Instead of treating all models as generalists and averaging their outputs, this approach treats them as specialists—each "voted in" only when market conditions favor their specific statistical bias.

## 2. Current State Assessment
Currently, the system uses a "Winner-Takes-Much" approach in `consensus_engine.py`:
- **Training:** Multiple models (XGBoost, RF, Linear Regression) are trained on the same features.
- **Evaluation:** A single "Score" (80% Directional Accuracy + 20% RMSE) determines a "Winner".
- **Execution:** The system calculates an ensemble average of all models.

> [!WARNING]
> **Current Weakness:** Simple averaging dilutes the precision of specialist models. If XGBoost is 90% accurate in high-volatility but Linear Regression is 40% accurate, the average (65%) is worse than the specialist's solo performance.

---

## 3. High-Performance Architecture (MoE)

### Phase 1: Model "Fingerprinting" (The Audit)
Instead of a single accuracy score, we must measure **Conditional Precision**. 
We track performance in specific "Market Regimes":

| Regime | Indicator | Expected Specialist |
| :--- | :--- | :--- |
| **Volatile** | ATR > 2.0 / Standard Deviation High | **XGBoost** (Handles sharp gradients) |
| **Mean Reverting** | RSI < 30 or > 70 | **Random Forest** (Handles non-linear returns) |
| **Trending (Quiet)** | ADX > 25 / Low Volatility | **Linear Regression** (Captures simple momentum) |
| **Regime Shift** | Volume Spikes > 2.5x | **LSTM / Deep Learning** (Captures sequence anomalies) |

### Phase 2: The "Gating Network" (The Router)
We implement a **Router** function. This is a logic layer that sits between the Data Pipeline and the Prediction Engine.

```python
def routing_logic(current_market_data):
    # Analyze the state
    volatility = calculate_historical_volatility(current_market_data)
    trend_strength = calculate_adx(current_market_data)
    
    if volatility > THRESHOLD_HIGH:
        return "XGBoost_Specialist"
    elif trend_strength < THRESHOLD_LOW:
        return "RandomForest_Specialist"
    else:
        return "Linear_Ensemble"
```

---

## 4. Implementation Step-by-Step

### 1. Enhanced Diagnostics
Modify `baseline_models.py` to save more granular metrics:
- `precision_on_positive_move`: How often is it right when it says UP?
- `precision_on_negative_move`: How often is it right when it says DOWN?
- `volatility_bracket_performance`: Performance in low/med/high volatility bins.

### 2. Specialist Training
Currently, all models see all data. In the new system:
- **XGBoost-V**: Trained only on "High Volatility" historical windows.
- **RF-S**: Trained only on "Sideways/Consolidating" historical windows.

### 3. The Execution Logic
Update `consensus_engine.py` to use a "Conditional Switch":
```diff
- final_change = np.mean([m.change_percent for m in models])
+ regime = self.judge_regime(df)
+ final_change = models[regime].change_percent
```

---

## 5. Hedge Fund "Gold Standard" Checklist
To implement this at a professional level, follow these constraints:

- [ ] **Symmetry Check:** Never use a model that has >10% gap between UP-precision and DOWN-precision (this indicates bias).
- [ ] **Complexity Penalty:** If a simple Linear model performs within 2% of XGBoost, **choose the Linear model**. Less complexity = less "model drift".
- [ ] **Regime Persistence:** Don't switch models every interval. Use a "Hysteresis" (a delay) to ensure the market regime has actually changed before switching specialists.

## 6. Next Steps for Implementation
1. **Infrastructure:** Create `algotrade_datascience/modeling/specialists/` directory.
2. **Data:** Add `Regime` tags to the training CSVs.
3. **Logic:** Re-run the `generate_complete_report.py` to compare "Generalist Consensus" vs "Specialist Routing".

---
*Created by Antigravity AI for FinAdvice Strategy Expansion.*
