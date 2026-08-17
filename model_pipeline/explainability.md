# Insights from feature importance tools

During this project, the advantage of using several model architectures, is that we can take advantage of several feature_importance tools such as:

1. Linear Coefficients (Linear/Lasso Regression)
2. Feature Importance (Tree-Based Algorithms)
3. SHAP (Tree-Based Algorithms)

These findings can be found on the feature_importance, shap_summary and shap_by_category .csvs in the model_pipeline/data/08_reporting folder. Furthermore, the main findings are summarised in the model_reporting.ipynb notebook

To summarise the main findings from these methods, these are the following.

1. The most important feature in determining delivery time is the delivery distance. On a lesser scale, the second most important variable is the preparation time. They have the higher coefficients, importance and shap values.

2. Other relevant features are the courier experience, if the traffic level is high/low, or is the weather is clear/snowy. This was verified by both the linear coefficients and the shap values of the tree-based models.

3. The lasso Regression provided three variables as non-contributing: 
    1) The weather being rainy.
    2) The time of day being night.
    3) The time of day being evening.
Although, Linear Regression finds these features to be relatively relevant, all other methods agree with the Lasso Regression findings that these features are not really determinant.

4. Overall, the type of vehicle used in the delivery was also found to be not a determining factor. Across all tests, none of the vehicles was found to have a high feature importance/shap value.

5. Null values in both the time of day and weather conditions were found to increase the delivery time by the high positive shap value. Further research needs to be done on whether this is the result of the low amount of data points (30 rows each), or because of external factors affecting their readings (i.e really late hours or emergency weather conditions)


