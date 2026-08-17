# Your modeling logic, metric choice, and tuning approach.

# Modeling Logic

In order to have a wide range of options, I decided to develop five models for the following reasons:
1. Linear Regression: Most simple and easiest to understand model
2. Lasso Regression: Similar to linear regression, but disregarding features that have no impact on the model.
3. Random Forest: Standard Tree-Based algorithm that takes advantage of randomness to identify patterns in the data.
4. XGBoost: Standard Tree-Based algorithm that perform a series of iterations to find out the best model.
5. CatBoost: Similar to XGBoost, but built specifically initially to handle categorical data, which this dataset contains.

In the end, the Lasso Regression model was the architecture with the lowest error metrics (Test RMSE = 10.63). This model architecture was benefitted from having a small number of features and data points to predict. It resulted in better results than the normal Linear Regression because it identified features that didn't contribute significantly, like the Time of Day being Evening/Night.
Although, it would be the selected choice for now, the CatBoost model (TEST RMSE = 11.12) is not significantly worse and, if in the future more features/datapoints are added for training, it could really benefit from the non-linear relationships 
between data and target that could be identified.

These results can be found on model_pipeline/data/08_reporting/summary_models.csv

# Metric Choice

Considering this is a regression problem that has an issue with large values in the target column, the chosen metric was Root Mean Square Error /RMSE.

This is because this metric punishes models that severely underpredict large values, compared to other metrics such as MAE. As explained in the EDA_report.md, this was something we needed to prevent to safeguard customer satisfaction.
As such, this was the metric that guided the training and hyperparameter tuning of the models.

Furthermore, additional metrics were chosen in order to compare the five models and provide more understanding. These were the following:
1. R2: For simplicity, and understanding how much of the data variance can be explained by the model.
2. Mean Absolute Error: To pair with RMSE, and understanding if there is a skewing in the model predictions.
3. Mean Absolute Percentage Error: To communicate to stakeholders the deviation of the model more easily. For example, the model is overestimating delivery times by 11%.

These results can be found on model_pipeline/data/08_reporting/summary_models.csv

# Tuning

Due to timing issues, the hyperparameter tuning was done relatively simply. The process can be found on hyperparameter_notebook.ipynb

For each of the model architectures that allow it (all but Linear Regression), 5 Fold Cross Validation was performed in order for the model architecture to find the best hyperparameters. This 5 Fold Cross Validation was done specifically on the training data (80% of the Dataset).

Furthermore, graphs were plotted of training RMSE vs test RMSE to find out the hyperparameter values were causing serious overfitting. An elbow test was performed in order to choose the parameters that would be fixed when training the model. The iterated parameters were the following:

## Lasso Regression

1 . Regularization Parameter

## Random Forest

1. Number of Estimator Trees
2. Minimum Samples per Leaf
3. Maximum Tree Depth

## XGBoost

1. Number of Estimator Trees
2. Maximum Tree Depth
3. Learning Rate

## CatBoost
1. Number of Estimator Trees
2. Maximum Tree Depth
3. Learning Rate
4. Regularization Parameter


Looking back, a Grid Search CV would be the more robust approach, but this method was followed in order to understand more deeply each stage of the tuning.