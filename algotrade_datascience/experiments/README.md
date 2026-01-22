# Model Experimentation Folder

This folder is dedicated to research, data exploration, and model experimentation using Jupyter Notebooks.

## Purpose
- Prototype new feature engineering ideas.
- Test different ML architectures (XGBoost, LightGBM, LSTM, etc.).
- Visualize results and compare model performance.

## Notebooks
- `model_experiment_v1.ipynb`: Initial baseline model using XGBoost with simple technical indicators.

## Best Practices
- Keep notebooks clean and documented.
- When an experiment is successful, migrate the stable logic to the `modeling/` or `features/` packages.
- Save large model weights or plotly exports in a `temp_results/` subfolder if necessary (ignored by git).
