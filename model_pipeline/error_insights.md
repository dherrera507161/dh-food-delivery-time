# Insights on when and why your models fails

## Model Weaknesses

The model has a weakness in predicting the following categories:

1. The model has a tendency to have a higher error in deliveries under rainy conditions. For Lasso Regression:(R2=0.61).
2. The model has a tendency to have a higher error in deliveries under high (R2=0.65) traffic.
3. The model has a tendency to have a higher error in deliveries made in scooters (R2=0.71).
4. The model does not know how to accurately predict null/unknown conditions.

These issues were found to be constant across all model architectures. 

## Reasons for Model Weakness

In general, I find the reasons of the model weaknesses to be the following:
1. The low amount of data (Only 1000 points) makes it really challenging for complex architectures to derive the non-linear relationships between data and target
2. Long-durations deliveries are less common in the dataset than short-ones. As such, the underprediction of deliveries will be a more common issue
3. Neither the high traffic, the rainy conditions or the scooters were the main dominant data value across their categories. As such, since the training data was not pre-selected to provide a fair split across datapoints, it is not surprising if these examples got overshadowed by the other, more common, data points.
4. Similarly, when the category is unknown (Traffic Condition/Weather), predictions are expected to be not as accurate due to their low amount of datapoints in the training set.

These findings were summarised on performance_analysis.ipynb