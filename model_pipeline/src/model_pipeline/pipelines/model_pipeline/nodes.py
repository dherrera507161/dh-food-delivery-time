"""
This is a boilerplate pipeline 'model_pipeline'
generated using Kedro 1.5.0
"""

from typing import Tuple

import pandas as pd
import numpy as np
import shap
from sklearn.model_selection import train_test_split, KFold
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

MAX_TIME = 300  # Prevent unreasonable hours from the API
CATEGORICAL_COLS = ["Weather", "Traffic_Level", "Time_of_Day", "Vehicle_Type"]
NUMERICAL_COLS = ["Distance_km", "Preparation_Time_min", "Courier_Experience_yrs"]


def prepare_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Remove implausible rows from the raw data.

    Args:
        raw_data: A pandas DataFrame containing the raw data.

    Returns:
        A pandas DataFrame with implausible rows removed.
    """
    df = raw_data.copy()
    delivery_time_col = "Delivery_Time_min"
    distance_col = "Distance_km"

    # This is to remove any unrealistic rows (e.g. negative distance, negative delivery time, or delivery time greater than 5 hours)
    df_filtered = df[
        (df[delivery_time_col] <= MAX_TIME)
        & (df[distance_col] > 0)
        & (df[delivery_time_col] > 0)
    ]

    # Fill missing categorical values with "Unknown"
    for col in CATEGORICAL_COLS:
        df_filtered[col] = df_filtered[col].fillna("Unknown")

    return df_filtered


def split_data(
    data: pd.DataFrame, parameters: dict
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into training and test sets.

    Args:
        data: Data to split.
        parameters: Parameters defined in parameters_model_pipeline.yml, expects
            "test_size" and "random_state".

    Returns:
        Split data: train_data, test_data.
    """
    train_data, test_data = train_test_split(
        data,
        test_size=parameters["test_size"],
        random_state=parameters["random_state"],
    )
    return train_data, test_data


def prepare_model_inputs(
    data: pd.DataFrame, parameters: dict
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare model inputs and target variable.

    Args:
        data: Data to prepare.
        parameters: Parameters defined in parameters_model_pipeline.yml, expects
            "target_column" and "index_column".

    Returns:
        Prepared model inputs and target variable.
    """
    X = data.drop(columns=[parameters["target_column"], parameters["index_column"]])
    y = data[parameters["target_column"]]
    return X, y


def build_native_model_input(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare model inputs for models that handle categorical features natively
    (e.g. XGBoost, CatBoost) by casting categorical columns to the pandas
    "category" dtype.

    Args:
        X_train: Training features.
        X_test: Test features.

    Returns:
        Train and test features with categorical columns cast to "category" dtype.
    """
    categorical_cols = X_train.select_dtypes(include="object").columns

    X_train_native = X_train.copy()
    X_test_native = X_test.copy()
    X_train_native[categorical_cols] = X_train_native[categorical_cols].astype(
        "category"
    )
    X_test_native[categorical_cols] = X_test_native[categorical_cols].astype("category")

    return X_train_native, X_test_native


def build_encoded_model_input(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare model inputs for models that cannot handle categorical features
    natively (e.g. Random Forest, Linear Regression): one-hot encode categorical
    columns and min-max scale numerical columns. The encoder and scaler are fit
    on the training data only and then applied to both train and test data, so
    test data never leaks into the fitting process.

    Args:
        X_train: Training features.
        X_test: Test features.

    Returns:
        Train and test features, one-hot encoded and min-max scaled.
    """
    # Categorical columns match those imputed in prepare_data; numerical columns
    # are the continuous features to be min-max scaled: distance, preparation
    # time, and courier experience.
    categorical_cols = CATEGORICAL_COLS
    numerical_cols = NUMERICAL_COLS

    # One category per column must be dropped: keeping all of them makes the
    # one-hot columns for a feature sum to 1 on every row, which is perfectly
    # collinear with the intercept (the "dummy variable trap") and breaks
    # Linear Regression. "Unknown" is dropped as the reference category when
    # present because it is an imputed placeholder for missing data, not an
    # observed traffic/weather/etc. level, so it shouldn't be a real feature
    # column; columns without an "Unknown" level fall back to dropping their
    # first category alphabetically.
    categories_to_drop = []
    for col in categorical_cols:
        categories = sorted(X_train[col].unique())
        categories_to_drop.append(
            "Unknown" if "Unknown" in categories else categories[0]
        )

    encoder = OneHotEncoder(
        handle_unknown="ignore", sparse_output=False, drop=categories_to_drop
    )
    encoder.fit(X_train[categorical_cols])
    encoded_cols = encoder.get_feature_names_out(categorical_cols)

    train_encoded_cat = pd.DataFrame(
        encoder.transform(X_train[categorical_cols]),
        columns=encoded_cols,
        index=X_train.index,
    )
    test_encoded_cat = pd.DataFrame(
        encoder.transform(X_test[categorical_cols]),
        columns=encoded_cols,
        index=X_test.index,
    )

    # Courier_Experience_yrs has missing values; fill them with the training
    # mean only (never the test set's own mean) so no test-set statistics leak
    # into feature construction, matching the encoder/scaler fit-on-train rule
    # above.
    train_numerical = X_train[numerical_cols].copy()
    test_numerical = X_test[numerical_cols].copy()
    courier_experience_mean = train_numerical["Courier_Experience_yrs"].mean()
    train_numerical["Courier_Experience_yrs"] = train_numerical[
        "Courier_Experience_yrs"
    ].fillna(courier_experience_mean)
    test_numerical["Courier_Experience_yrs"] = test_numerical[
        "Courier_Experience_yrs"
    ].fillna(courier_experience_mean)

    scaler = MinMaxScaler()
    scaler.fit(train_numerical)

    train_scaled_num = pd.DataFrame(
        scaler.transform(train_numerical),
        columns=numerical_cols,
        index=X_train.index,
    )
    test_scaled_num = pd.DataFrame(
        scaler.transform(test_numerical),
        columns=numerical_cols,
        index=X_test.index,
    )

    X_train_encoded = pd.concat([train_scaled_num, train_encoded_cat], axis=1)
    X_test_encoded = pd.concat([test_scaled_num, test_encoded_cat], axis=1)

    return X_train_encoded, X_test_encoded


def _extract_target(y, parameters: dict) -> np.ndarray:
    """Flatten a target table loaded from the catalog into a 1D array.

    Datasets round-tripped through the catalog come back as a single-column
    DataFrame rather than the Series a node may have returned, so select the
    target column explicitly by name instead of assuming a Series.
    """
    if isinstance(y, pd.DataFrame):
        return y[parameters["target_column"]].to_numpy()
    return np.asarray(y).ravel()


def train_linear_regression(
    X_train: pd.DataFrame, y_train: pd.DataFrame, parameters: dict
) -> LinearRegression:
    """Train a Linear Regression model."""
    model = LinearRegression()
    model.fit(X_train, _extract_target(y_train, parameters))
    return model


def _make_kfold(parameters: dict) -> KFold:
    return KFold(
        n_splits=parameters["cv_folds"],
        shuffle=True,
        random_state=parameters["random_state"],
    )


def train_lasso_regression(
    X_train: pd.DataFrame, y_train: pd.DataFrame, parameters: dict
) -> LassoCV:
    """Train a Lasso Regression model using LassoCV with alpha pinned to a
    single fixed value.

    LassoCV always performs cross-validation internally as part of fit();
    passing a single-value "alphas" list keeps that CV machinery (and the
    5-fold CV convention used throughout this pipeline) while making the
    selected alpha deterministic rather than searched.
    """
    model = LassoCV(alphas=[parameters["lasso"]["alpha"]], cv=_make_kfold(parameters))
    model.fit(X_train, _extract_target(y_train, parameters))
    return model


def _build_random_forest(parameters: dict) -> RandomForestRegressor:
    return RandomForestRegressor(
        random_state=parameters["random_state"],
        min_samples_leaf=parameters["random_forest"]["min_samples_leaf"],
        max_depth=parameters["random_forest"]["max_depth"],
    )


def _build_xgboost(parameters: dict) -> XGBRegressor:
    return XGBRegressor(
        random_state=parameters["random_state"],
        enable_categorical=True,
        importance_type="gain",
        max_depth=parameters["xgboost"]["max_depth"],
        learning_rate=parameters["xgboost"]["learning_rate"],
    )


def _build_catboost(parameters: dict) -> CatBoostRegressor:
    return CatBoostRegressor(
        random_state=parameters["random_state"],
        cat_features=CATEGORICAL_COLS,
        verbose=False,
        allow_writing_files=False,
        depth=parameters["catboost"]["depth"],
        l2_leaf_reg=parameters["catboost"]["l2_leaf_reg"],
    )


def _run_kfold_cv(
    build_model, X: pd.DataFrame, y_values: np.ndarray, parameters: dict
) -> dict:
    """K-fold cross-validate a model type, building a fresh model per fold.

    A manual loop (rather than sklearn's cross_validate, which relies on
    clone()) is used because CatBoostRegressor's constructor does not
    round-trip cleanly through sklearn's clone().

    Args:
        build_model: A callable(parameters) -> unfitted regressor.
        X: Training features.
        y_values: Training target as a 1D array.
        parameters: Parameters defined in parameters_model_pipeline.yml, expects
            "cv_folds" and "random_state".

    Returns:
        A dict with the mean "R2", "MAE", "MAPE", and "RMSE" across folds.
    """
    kfold = _make_kfold(parameters)
    r2_scores, mae_scores, mape_scores, rmse_scores = [], [], [], []
    for train_idx, test_idx in kfold.split(X):
        X_fold_train, X_fold_test = X.iloc[train_idx], X.iloc[test_idx]
        y_fold_train, y_fold_test = y_values[train_idx], y_values[test_idx]

        fold_model = build_model(parameters)
        fold_model.fit(X_fold_train, y_fold_train)
        y_fold_pred = fold_model.predict(X_fold_test)

        r2_scores.append(r2_score(y_fold_test, y_fold_pred))
        mae_scores.append(mean_absolute_error(y_fold_test, y_fold_pred))
        mape_scores.append(mean_absolute_percentage_error(y_fold_test, y_fold_pred))
        rmse_scores.append(root_mean_squared_error(y_fold_test, y_fold_pred))

    return {
        "R2": float(np.mean(r2_scores)),
        "MAE": float(np.mean(mae_scores)),
        "MAPE": float(np.mean(mape_scores)),
        "RMSE": float(np.mean(rmse_scores)),
    }


def train_random_forest(
    X_train: pd.DataFrame, y_train: pd.DataFrame, parameters: dict
) -> RandomForestRegressor:
    """Train a Random Forest Regressor, K-fold cross-validating it first."""
    y_values = _extract_target(y_train, parameters)
    cv_scores = _run_kfold_cv(_build_random_forest, X_train, y_values, parameters)
    print(f"Random Forest {parameters['cv_folds']}-fold CV metrics: {cv_scores}")

    model = _build_random_forest(parameters)
    model.fit(X_train, y_values)
    return model


def train_xgboost(
    X_train: pd.DataFrame, y_train: pd.DataFrame, parameters: dict
) -> XGBRegressor:
    """Train an XGBoost Regressor, K-fold cross-validating it first."""
    y_values = _extract_target(y_train, parameters)
    cv_scores = _run_kfold_cv(_build_xgboost, X_train, y_values, parameters)
    print(f"XGBoost {parameters['cv_folds']}-fold CV metrics: {cv_scores}")

    model = _build_xgboost(parameters)
    model.fit(X_train, y_values)
    return model


def train_catboost(
    X_train: pd.DataFrame, y_train: pd.DataFrame, parameters: dict
) -> CatBoostRegressor:
    """Train a CatBoost Regressor, K-fold cross-validating it first."""
    y_values = _extract_target(y_train, parameters)
    cv_scores = _run_kfold_cv(_build_catboost, X_train, y_values, parameters)
    print(f"CatBoost {parameters['cv_folds']}-fold CV metrics: {cv_scores}")

    model = _build_catboost(parameters)
    model.fit(X_train, y_values)
    return model


def generate_predictions(
    model, X_test: pd.DataFrame, y_test: pd.DataFrame, parameters: dict
) -> pd.DataFrame:
    """Generate predictions for a fitted model on the test set.

    Args:
        model: A fitted regressor implementing predict().
        X_test: Test features.
        y_test: Test target.
        parameters: Parameters defined in parameters_model_pipeline.yml, expects
            "target_column".

    Returns:
        A DataFrame with "y_true" and "y_pred" columns.
    """
    y_true = _extract_target(y_test, parameters)
    y_pred = model.predict(X_test)
    return pd.DataFrame({"y_true": y_true, "y_pred": y_pred}, index=X_test.index)


def _compute_metrics_table(predictions_by_model: dict) -> pd.DataFrame:
    """Build a "Metric" x model table of R2, MAE, MAPE, and RMSE.

    Args:
        predictions_by_model: Mapping of model display name to its
            "y_true"/"y_pred" predictions table.

    Returns:
        A DataFrame with a "Metric" column (R2, MAE, MAPE, RMSE) and one
        column per model.
    """
    summary = {}
    for model_name, predictions in predictions_by_model.items():
        y_true = predictions["y_true"]
        y_pred = predictions["y_pred"]
        summary[model_name] = {
            "R2": r2_score(y_true, y_pred),
            "MAE": mean_absolute_error(y_true, y_pred),
            "MAPE": mean_absolute_percentage_error(y_true, y_pred),
            "RMSE": root_mean_squared_error(y_true, y_pred),
        }

    table = pd.DataFrame(summary)
    table.index.name = "Metric"
    return table.reset_index()


def build_summary_table(
    pred_train_linear_regression: pd.DataFrame,
    pred_test_linear_regression: pd.DataFrame,
    pred_train_lasso_regression: pd.DataFrame,
    pred_test_lasso_regression: pd.DataFrame,
    pred_train_random_forest: pd.DataFrame,
    pred_test_random_forest: pd.DataFrame,
    pred_train_xgboost: pd.DataFrame,
    pred_test_xgboost: pd.DataFrame,
    pred_train_catboost: pd.DataFrame,
    pred_test_catboost: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize R2, MAE, MAPE, and RMSE for each trained model, on both the
    training and test sets.

    Args:
        pred_train_<model>: "y_true"/"y_pred" table for <model> on the
            training set.
        pred_test_<model>: "y_true"/"y_pred" table for <model> on the test
            set.

    Returns:
        A DataFrame with "Dataset" (Train/Test) and "Metric" (R2, MAE, MAPE,
        RMSE) columns, and one column per model.
    """
    train_table = _compute_metrics_table(
        {
            "Linear Regression": pred_train_linear_regression,
            "Lasso Regression": pred_train_lasso_regression,
            "Random Forest": pred_train_random_forest,
            "XGBoost": pred_train_xgboost,
            "CatBoost": pred_train_catboost,
        }
    )
    train_table.insert(0, "Dataset", "Train")

    test_table = _compute_metrics_table(
        {
            "Linear Regression": pred_test_linear_regression,
            "Lasso Regression": pred_test_lasso_regression,
            "Random Forest": pred_test_random_forest,
            "XGBoost": pred_test_xgboost,
            "CatBoost": pred_test_catboost,
        }
    )
    test_table.insert(0, "Dataset", "Test")

    return pd.concat([train_table, test_table], ignore_index=True).round(2)


def build_coefficient_table(
    model, X_train: pd.DataFrame, value_name: str
) -> pd.DataFrame:
    """Build a per-feature coefficient/importance table for a fitted model.

    Args:
        model: A fitted regressor exposing "coef_" (Linear/Lasso) or
            "feature_importances_" (Random Forest/XGBoost/CatBoost).
        X_train: The features table the model was fit on, used only for
            column names/order.
        value_name: Column name for the per-feature values (e.g.
            "Coefficient" or "Gain").

    Returns:
        A DataFrame with "Feature" and value_name columns.
    """
    values = model.coef_ if hasattr(model, "coef_") else model.feature_importances_
    return pd.DataFrame({"Feature": X_train.columns, value_name: values}).round(3)


def build_coefficient_table_linear_regression(
    model, X_train: pd.DataFrame
) -> pd.DataFrame:
    """Coefficient table for the Linear Regression model."""
    return build_coefficient_table(model, X_train, "Coefficient")


def build_coefficient_table_lasso_regression(
    model, X_train: pd.DataFrame
) -> pd.DataFrame:
    """Coefficient table for the Lasso Regression model."""
    return build_coefficient_table(model, X_train, "Coefficient")


def build_coefficient_table_random_forest(model, X_train: pd.DataFrame) -> pd.DataFrame:
    """Feature importance table for the Random Forest model."""
    return build_coefficient_table(model, X_train, "Importance")


def build_coefficient_table_xgboost(model, X_train: pd.DataFrame) -> pd.DataFrame:
    """Gain importance table for the XGBoost model."""
    return build_coefficient_table(model, X_train, "Gain")


def build_coefficient_table_catboost(model, X_train: pd.DataFrame) -> pd.DataFrame:
    """Feature importance table for the CatBoost model."""
    return build_coefficient_table(model, X_train, "Importance")


def build_shap_summary_table(model, X: pd.DataFrame) -> pd.DataFrame:
    """Compute mean signed and mean absolute SHAP values per feature for a
    tree-based regressor.

    SHAP values for a regression model are denominated in the model's output
    units directly (minutes of predicted Delivery_Time_min here), so each
    value already reads as "this feature moves the prediction by X minutes"
    with no unit conversion needed.

    Args:
        model: A fitted tree-based regressor (Random Forest, XGBoost, or
            CatBoost).
        X: Features to explain (test set).

    Returns:
        A DataFrame with "Feature", "Mean SHAP Value", and "Mean Absolute
        SHAP Value" columns.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return pd.DataFrame(
        {
            "Feature": X.columns,
            "Mean SHAP Value": shap_values.mean(axis=0),
            "Mean Absolute SHAP Value": np.abs(shap_values).mean(axis=0),
        }
    ).round(3)


def build_shap_by_category_table(model, X: pd.DataFrame) -> pd.DataFrame:
    """Break down each categorical feature's mean signed and mean absolute
    SHAP value by its observed category values, for models using native
    categorical columns (XGBoost, CatBoost).

    A single feature-level mean SHAP value blends together every category a
    row could have, weighted by how often each category occurs in the data --
    which can hide, for example, that Traffic_Level=High raises the predicted
    delivery time while Traffic_Level=Low lowers it. Grouping by the actual
    category value observed in each row surfaces that per-value effect
    directly, in minutes of predicted delivery time.

    Args:
        model: A fitted tree-based regressor using native categorical
            columns (XGBoost or CatBoost).
        X: Features to explain (test set), with raw categorical columns.

    Returns:
        A DataFrame with "Feature", "Category Value", "Mean SHAP Value", and
        "Mean Absolute SHAP Value" columns.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = pd.DataFrame(
        explainer.shap_values(X), columns=X.columns, index=X.index
    )

    rows = []
    for col in CATEGORICAL_COLS:
        for category_value in sorted(X[col].unique()):
            group_shap = shap_values.loc[X[col] == category_value, col]
            rows.append(
                {
                    "Feature": col,
                    "Category Value": category_value,
                    "Mean SHAP Value": group_shap.mean(),
                    "Mean Absolute SHAP Value": group_shap.abs().mean(),
                }
            )

    return pd.DataFrame(rows).round(3)
