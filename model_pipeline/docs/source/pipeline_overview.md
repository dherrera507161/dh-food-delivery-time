# Pipeline Overview

The `model_pipeline` Kedro pipeline
(`src/model_pipeline/pipelines/model_pipeline/pipeline.py`) is assembled from
four sub-pipelines, summed together:

```python
data_preparation_pipeline + training_pipeline + evaluation_pipeline + reporting_pipeline
```

Training, evaluation, and per-model reporting nodes are generated from a
single `MODELS` config dict (one entry per model), rather than being
hand-written per model — see the `MODELS` dict at the top of `pipeline.py`
for the exact per-model wiring (which model-input table each one trains on,
and which reporting nodes it gets).

## 1. Data Preparation

Cleans the raw data, splits it into train/test, and builds two parallel
model-input tables: one for models that handle categorical features natively
(XGBoost, CatBoost), and one for models that need one-hot encoding (Linear
Regression, Lasso Regression, Random Forest).

| Node | Function | Description |
| --- | --- | --- |
| `prepare_data_node` | `prepare_data` | Removes implausible rows (non-positive distance, delivery time outside `(0, MAX_TIME]`) and fills missing categorical values with `"Unknown"`. |
| `split_data_node` | `split_data` | Splits the cleaned data into train/test sets (`test_size`, `random_state` from `params:model_options`). |
| `prepare_train_model_inputs_node` / `prepare_test_model_inputs_node` | `prepare_model_inputs` | Splits each set into features (X) and target (y), dropping the index and target columns. |
| `build_native_model_input_node` | `build_native_model_input` | Casts categorical columns to pandas `"category"` dtype, for XGBoost/CatBoost. |
| `build_encoded_model_input_node` | `build_encoded_model_input` | One-hot encodes categorical columns (dropping `"Unknown"`, or the alphabetically-first level, as the reference category) and min-max scales numerical columns, fit on train only. Also imputes missing `Courier_Experience_yrs` with the training mean. |

## 2. Model Training

Trains all 5 regressors. Random Forest, XGBoost, and CatBoost are each
K-fold cross-validated (`cv_folds` in `params:model_options`, currently 5)
via a manual per-fold loop before the final fit, with the fold-mean R2/MAE/
MAPE/RMSE printed to the console. Lasso Regression uses `LassoCV` with the
alpha search space pinned to a single fixed value (`params:model_options
.lasso.alpha`), so the same CV machinery still runs, but the selected alpha
is deterministic rather than searched.

| Node | Function | Model input | Hyperparameters (from `params:model_options`) |
| --- | --- | --- | --- |
| `train_linear_regression_node` | `train_linear_regression` | `modin_train_encoded_categorical` | none |
| `train_lasso_regression_node` | `train_lasso_regression` | `modin_train_encoded_categorical` | `lasso.alpha` |
| `train_random_forest_node` | `train_random_forest` | `modin_train_encoded_categorical` | `random_forest.min_samples_leaf`, `random_forest.max_depth` |
| `train_xgboost_node` | `train_xgboost` | `modin_train_native_categorical` | `xgboost.max_depth`, `xgboost.learning_rate` |
| `train_catboost_node` | `train_catboost` | `modin_train_native_categorical` | `catboost.depth`, `catboost.l2_leaf_reg` |

## 3. Model Evaluation

Generates predictions for every model on both the training set and the test
set, using the shared `generate_predictions` function. The train-set
predictions exist specifically to support the train-vs-test comparison in
`summary_models` (see Reporting below).

| Node pattern | Function | Description |
| --- | --- | --- |
| `predict_<model>_node` (x5) | `generate_predictions` | Test-set predictions (`y_true`/`y_pred`) for each model. |
| `predict_train_<model>_node` (x5) | `generate_predictions` | Training-set predictions for each model. |

## 4. Reporting

Builds the comparison tables persisted under `data/08_reporting/`, consumed
by the project's Jupyter notebooks (see below).

| Node pattern | Function | Description |
| --- | --- | --- |
| `build_summary_table_node` | `build_summary_table` | R2/MAE/MAPE/RMSE per model, on both train and test sets (`Dataset` column distinguishes the two). |
| `build_coefficient_table_<model>_node` (x5) | `build_coefficient_table_*` | Per-feature coefficient (Linear/Lasso) or importance (Random Forest/XGBoost/CatBoost gain) table. |
| `build_shap_summary_table_<model>_node` (Random Forest, XGBoost, CatBoost) | `build_shap_summary_table` | Mean signed and mean absolute SHAP value per feature. |
| `build_shap_by_category_table_<model>_node` (XGBoost, CatBoost only) | `build_shap_by_category_table` | Mean SHAP value broken down by each observed category value, for the 4 categorical features. Not produced for Random Forest, since its categorical features are already split into one-hot dummy columns rather than a single raw categorical column. |

## Notebooks

Three notebooks under `notebooks/` build on top of this pipeline's catalog
outputs. Run them via `kedro jupyter notebook` (or `kedro jupyter lab`) from
the project root so the `catalog` variable is available (or run
`%load_ext kedro.ipython` inside a plain Jupyter session).

- **`model_reporting.ipynb`** — predicted vs actual scatter plots for all 5
  models, SHAP violin plots for the tree-based models, and per-category SHAP
  bar charts for XGBoost/CatBoost (built from `shap_by_category_xgboost`/
  `shap_by_category_catboost`, not recomputed).
- **`hyperparameter_notebook.ipynb`** — train vs test RMSE validation curves
  as individual hyperparameters are swept (Random Forest: `n_estimators`,
  `min_samples_leaf`, `max_depth`; XGBoost: `n_estimators`, `max_depth`,
  `learning_rate`; CatBoost: `iterations`, `learning_rate`, `depth`,
  `l2_leaf_reg`; Lasso: `alpha`).
- **`performance_analysis.ipynb`** — predicted vs actual scatter plots
  faceted by `Traffic_Level`/`Weather`/`Vehicle_Type`, with R2 shown per
  facet, for all 5 models.
