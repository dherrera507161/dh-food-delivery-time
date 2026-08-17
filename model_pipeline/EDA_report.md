# Key patterns, outliers, and assumptions you made.

For the following exercise, I have detected the following important information:

## Key patterns between Features

There are no strong relationships between two features as evidenced by a correlation matrix in the notebook: eda_correlation_analysis.ipynb. There is no evidence why there should be any feature removal in this data


## Key relations between feature and target
From basic scatterplots, I can visually identify the following relationships:
1. There is a strong positive correlation between distance and delivery time
2. There is weaker, but not still noticeable positive correlation between preparation time and delivery time.
3. There is also a noticeable effect of traffic size. As expected, as the traffic conditions worsens, delivery time is expected to increase.
4. All other features did not present a clear linear relationship just from looking at scatterplots that related each feature to the target

## Feature Outliers

For none of the numerical features, there seems to be any outlier values.

1. Distance KM. Min Value: 0.59 km . Mean Value: 10.06 km. Max Value: 19.99 km. Range= Mean +- 3D = [-7.03,27.15]
2. Preparation Time. Min Value: 5.00 min . Mean Value: 16.98 min. Max Value: 29.00 min. Range= Mean +- 3D = [-4.63,38.60]
3. Courier Experience . Min Value: 0 years . Mean Value: 4.58 years. Max Value: 9.00 years. Range= Mean +- 3D = [-4.16,13.32]

## Target Outliers

The target is another story, in theory, there are values that need to be filtrated out according to most common practices:

1. Delivery Time. Min Value: 8 min . Mean Value: 56.73 min. Max Value: 153 min. Range= Mean +- 3D = [-9.48,122.94]
For example, as there are values above 122.94 minutes in the data, they are eligible to be removed.
Nevertheless, as stated in the assumptions, there is a performance-based reason to keep long delivery times in the training and testing data of the model.

## Assumptions
After observing the data, I have assumed the following statements:
1. All of the records are coming from clean, reliable data and there are no abnormal readings. As such, I should not filter out any of the rows present in the data despite some being over 2 hours of delivery time.
2. On the first point, I am assuming that incorrectly identifying lengthy deliveries would be damaging to the business. As such, I must include examples of late deliveries even if they do not fall on the standard outlier test rules
3. If I see a future record with a delivery time of over 5 hours, I will assume it does come from an inadequate data extraction.
4. All null values are due to a empty reading from the source that collected that specific data type. I cannot infer, or assume any value based on this. For example, if the courier years of experience column is a null, I cannot just assume zero.
5. Assuming the model cannot be inputted nulls as a value, the best way for me to process categorical nulls is to create another category. 
6. In a similar situation, the best way for me to process numerical nulls is to just make them equal to the average of the training dataset.
7. In models that can handle null input values, it is better for the performance to leave them untouched.
8. The adequate train/test split for this situation is 80/20.