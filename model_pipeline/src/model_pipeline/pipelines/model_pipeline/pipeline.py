"""
This is a boilerplate pipeline 'model_pipeline'
generated using Kedro 1.5.0
"""

from kedro.pipeline import Node, Pipeline, pipeline  # noqa
from .nodes import (  # noqa: F401
    prepare_data,
    split_data,
    prepare_model_inputs,
    build_native_model_input,
    build_encoded_model_input,
    train_linear_regression,
    train_lasso_regression,
    train_random_forest,
    train_xgboost,
    train_catboost,
    generate_predictions,
    build_summary_table,
    build_coefficient_table_linear_regression,
    build_coefficient_table_lasso_regression,
    build_coefficient_table_random_forest,
    build_coefficient_table_xgboost,
    build_coefficient_table_catboost,
    build_shap_summary_table,
    build_shap_by_category_table,
)

ENCODED_TRAIN_INPUT = "modin_train_encoded_categorical"
ENCODED_TEST_INPUT = "modin_test_encoded_categorical"
NATIVE_TRAIN_INPUT = "modin_train_native_categorical"
NATIVE_TEST_INPUT = "modin_test_native_categorical"

# Per-model config driving the training/evaluation/reporting node loops below.
# "tree_based" gets a SHAP summary table; "shap_by_category" (native
# categorical models only) also gets the per-category-value SHAP breakdown.
MODELS = {
    "linear_regression": {
        "train_func": train_linear_regression,
        "coefficient_func": build_coefficient_table_linear_regression,
        "train_input": ENCODED_TRAIN_INPUT,
        "test_input": ENCODED_TEST_INPUT,
        "tree_based": False,
        "shap_by_category": False,
    },
    "lasso_regression": {
        "train_func": train_lasso_regression,
        "coefficient_func": build_coefficient_table_lasso_regression,
        "train_input": ENCODED_TRAIN_INPUT,
        "test_input": ENCODED_TEST_INPUT,
        "tree_based": False,
        "shap_by_category": False,
    },
    "random_forest": {
        "train_func": train_random_forest,
        "coefficient_func": build_coefficient_table_random_forest,
        "train_input": ENCODED_TRAIN_INPUT,
        "test_input": ENCODED_TEST_INPUT,
        "tree_based": True,
        "shap_by_category": False,
    },
    "xgboost": {
        "train_func": train_xgboost,
        "coefficient_func": build_coefficient_table_xgboost,
        "train_input": NATIVE_TRAIN_INPUT,
        "test_input": NATIVE_TEST_INPUT,
        "tree_based": True,
        "shap_by_category": True,
    },
    "catboost": {
        "train_func": train_catboost,
        "coefficient_func": build_coefficient_table_catboost,
        "train_input": NATIVE_TRAIN_INPUT,
        "test_input": NATIVE_TEST_INPUT,
        "tree_based": True,
        "shap_by_category": True,
    },
}


def create_pipeline(**kwargs) -> Pipeline:
    data_preparation_pipeline = pipeline(
        [
            Node(
                func=prepare_data,  # noqa: F821
                inputs="raw_food_delivery",
                outputs="int_food_delivery",
                name="prepare_data_node",
            ),
            Node(
                func=split_data,
                inputs=["int_food_delivery", "params:model_options"],
                outputs=["pri_train_food_delivery", "pri_test_food_delivery"],
                name="split_data_node",
            ),
            Node(
                func=prepare_model_inputs,
                inputs=["pri_train_food_delivery", "params:model_options"],
                outputs=["fea_train_features", "fea_train_tgt"],
                name="prepare_train_model_inputs_node",
            ),
            Node(
                func=prepare_model_inputs,
                inputs=["pri_test_food_delivery", "params:model_options"],
                outputs=["fea_test_features", "fea_test_tgt"],
                name="prepare_test_model_inputs_node",
            ),
            Node(
                func=build_native_model_input,
                inputs=["fea_train_features", "fea_test_features"],
                outputs=[NATIVE_TRAIN_INPUT, NATIVE_TEST_INPUT],
                name="build_native_model_input_node",
            ),
            Node(
                func=build_encoded_model_input,
                inputs=["fea_train_features", "fea_test_features"],
                outputs=[ENCODED_TRAIN_INPUT, ENCODED_TEST_INPUT],
                name="build_encoded_model_input_node",
            ),
        ],
        tags=["data_preparation", "model_pipeline"],
    )

    training_pipeline = pipeline(
        [
            Node(
                func=config["train_func"],
                inputs=[config["train_input"], "fea_train_tgt", "params:model_options"],
                outputs=f"model_{model_key}",
                name=f"train_{model_key}_node",
            )
            for model_key, config in MODELS.items()
        ],
        tags=["model_training", "model_pipeline"],
    )

    evaluation_nodes = []
    for model_key, config in MODELS.items():
        evaluation_nodes.append(
            Node(
                func=generate_predictions,
                inputs=[
                    f"model_{model_key}",
                    config["test_input"],
                    "fea_test_tgt",
                    "params:model_options",
                ],
                outputs=f"modout_prediction_{model_key}",
                name=f"predict_{model_key}_node",
            )
        )
        evaluation_nodes.append(
            Node(
                func=generate_predictions,
                inputs=[
                    f"model_{model_key}",
                    config["train_input"],
                    "fea_train_tgt",
                    "params:model_options",
                ],
                outputs=f"modout_prediction_train_{model_key}",
                name=f"predict_train_{model_key}_node",
            )
        )
    evaluation_pipeline = pipeline(
        evaluation_nodes, tags=["model_output", "model_pipeline"]
    )

    reporting_nodes = [
        Node(
            func=build_summary_table,
            inputs=[
                dataset_name
                for model_key in MODELS
                for dataset_name in (
                    f"modout_prediction_train_{model_key}",
                    f"modout_prediction_{model_key}",
                )
            ],
            outputs="summary_models",
            name="build_summary_table_node",
        ),
    ]
    for model_key, config in MODELS.items():
        reporting_nodes.append(
            Node(
                func=config["coefficient_func"],
                inputs=[f"model_{model_key}", config["train_input"]],
                outputs=f"feature_importance_{model_key}",
                name=f"build_coefficient_table_{model_key}_node",
            )
        )
        if config["tree_based"]:
            reporting_nodes.append(
                Node(
                    func=build_shap_summary_table,
                    inputs=[f"model_{model_key}", config["test_input"]],
                    outputs=f"shap_summary_{model_key}",
                    name=f"build_shap_summary_table_{model_key}_node",
                )
            )
        if config["shap_by_category"]:
            reporting_nodes.append(
                Node(
                    func=build_shap_by_category_table,
                    inputs=[f"model_{model_key}", config["test_input"]],
                    outputs=f"shap_by_category_{model_key}",
                    name=f"build_shap_by_category_table_{model_key}_node",
                )
            )
    reporting_pipeline = pipeline(
        reporting_nodes, tags=["model_evaluation", "model_pipeline"]
    )

    return (
        data_preparation_pipeline
        + training_pipeline
        + evaluation_pipeline
        + reporting_pipeline
    )
