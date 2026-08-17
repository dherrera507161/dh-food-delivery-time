# In strategic_reflections.md, answer the following questions
## 1. Model Failure: Your model underestimates delivery time on rainy days. Do you fix the model, the data, or the business expectations?

In reality, the answer is never 100% absolute. In honesty, there are solutions across different categories that I could implement. For example:
1. Related to the model:
    a) I could improve the quality of the training data by sampling it across the weather categories to ensure I give equal importance to all weather conditions, rather than depend on the distribution of the data.
    b) I could make a separate model focused specifically on predicting rainy conditions.
    c) I could do a model_calibration step in the pipeline, that ensures that the model prediction value are calibrated against a dataset with only deliveries in rainy conditions. For example, I could use histogram binning or isotonic regression to carry out this calibration step.

2. Related to the data:
    a) I could look for additional data in order to have more training examples so the model is able to learn from more points.
    b) I could research to see if the training data from rainy days was collected way before the rainy testing data. This could mean there is considerable data drift between my two datasets and worsen the prediction. 

3. Related to the business:
    a) I could comunicate the overall value that the model is brining to the business by improving the predictions across all categories, not only focusing on the rainy one.
    b) I could ask for more time to implement the previous solutions/collect more datapoints
    c) While the fixes are underway, I could adjust the output (i.e. correction to the underprediction, provide an estimated range) so the business is still able to act on the data while acknowledging the weakness of the model.

## 2. Transferability: The model performs well in Mumbai. It’s now being deployed in São Paulo. How do you ensure generalization?

To ensure generalization I would ask the following questions:
1. Are the weather conditions similar in Sao Paulo vs Mumbai?
2. Are the traffic conditions similar in Sao Paulo vs Mumbai?
3. Are the delivery vehicles used in a similar way in both countries?
4. Without changing anything, do the test metrics in Mumbai look similar to Sao Paulo?

If these features are not the same, I would probably have to adjust the ratio of the training data/add more data in order to match the distributions of these features to the ones that would be seen in Brazil.
Furthermore, since Distance is such an overwhelming feature, perhaps I would have to reframe the variable is expressed to a relative term rather than an absolute to ensure it is transferrable between regions. For example, input distance data as the ratio of distance/avg_delivery_distance where the average changes from region to region. 

## 3. GenAI Disclosure: Generative AI tools are a great resource that can facilitate development, what parts of this project did you use GenAI tools for? How did you validate or modify their output?

In this project, and in my professional coding, I use GenAI tools to give myself more time for the creative aspects of Data Science (such as choosing which models to consider and defining the pipeline to use). 
In this case, I have used it to:
1. Create artificial data for the SQL questions.
2. Summarise and document the code in the model_pipeline codespace.
3. Organise and condense the code in the model_pipeline codespace to make it more readable for the reviewer.
4. Consult it for the additional points in the assignment, such as the extra SQL queries for the insights.md and the API question.

To validate its output, I follow the following rules:
1. To not let it write code unsupervised and to ask for manual supervision for every change.
2. To ask for changes in small, testable steps that I can run in the terminal to verify its output.
3. To use separate online material/common judgement/other AI tools to judge its response.


## 4. Your Signature Insight: What's one non-obvious insight or decision you're proud of from this project?

My non-obvious insight is thanks to the Lasso Regression model. 
In an era where everyone wants to create and follow the biggest and more expensive models, I was surprised that my decision to test a simpler and less computationally expensive model paid off. In the end, the Lasso Regression model was the architecture with the lowest error metrics (Test RMSE = 10.63). This model architecture was benefitted from having a small number of features and data points to predict. In contrast, the CatBoost model (TEST RMSE = 11.12) is not significantly worse and, if in the future more features/datapoints are added for training, it could really benefit from the non-linear relationships 
between data and target that could be identified.

Furthermore, it was also really interesting to use it to detect which of all the variables (e.g. Time of Day) were mostly simply contributing noise to the dataset and could actually be removed from the model entirely. More Ssecifcally:
    1) The weather being rainy.
    2) The time of day being night.
    3) The time of day being evening.


## 5. Going to Production: How would you deploy your model to production? What other components would you need to include/develop in your codebase? Please be as detailed each step of the process, and feel free to showcase some of these components in the codebase.

When going to production, this would be the steps that I add to my codebase:
1. Pipeline Management Library: Rather than using notebooks in order to run the code, it would be better to implement the code using a system that divides the code into nodes and pipelines. This has already been implemented in the current code base through the use of the Kedro library. The benefit of this is to make the code easily reviewable while keeping a native .py format across the main parts of the code.

2. To utilise cloud tools, for example (MLFlow for model registry, AWS S3 for file storage) to ensure secure collaborations between multiple team members rather than having to replicate the code locally in everyone's computer separately.

3. A Monitoring Dashboard that shows the current performance of the model vs historical metrics and detects if the model performance is increasing/decreasing across time. Furthermore, it should also monitor the features of the model if we should be concerned about data drift.

4. A model calibration pipeline/ better segmentation of the data to allow for the model to improve the prediction of categories which do not have multiple data points. 

5. A CI/CD platform that allows multiple users to contribute to the codebase, but at the same time, ensures that the standards of the code are maintained through the multiple Pull Requests required to make the codebase grow.

6. The use of apps similar to Docker to ensure that the code is able to easily be run across different computers and clusters with minimal setup inconveniences.

7. The use of libraries such as Pyspark if the dataset is so big that it warrants the use of libraries that use distributed computing rather than use pandas which stay in memory.

8. The use of Terraform to establish the infrastructure of computing clusters if the size of the model grows large enough to warrant it.

9. The addition of an API layer to ensure that incoming data can be read automatically rather than depending on manual uploads.

10. The addition of unit tests to ensure that the data is being uploaded with the correct schema and the current code is able to handle it.

11. To consider the use of AutoML for better training of the current tree-based model and the training of champion models if the performance metrics of the current model decrease across time.