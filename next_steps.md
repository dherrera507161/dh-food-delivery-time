# NEXT STEPS FOR AN API PROTOTYPE

In order to create an API prototype, these are the steps I would follow to push one into production:

1. Register the winning model (Lasso) into a model registry service, such as MLFlow.

2. Create unit tests that ensure that the upcoming data matches the necessary schema and feature values necessary to make a correct prediction

3. Build an API that, after receiving a request with the adequate schema, utilises the model and the unit tests previously mentioned to provide a single response (the delivery time) for every data row.

4. Add a health-check point to confirm that the API is running correctly

5. Containerise the code to ensure that the code runs well across many different environments without mismatching dependencies.

6. Ensure that the API can both receive and deliver online requests, not just local ones. Ensure also that the protection layers work adequately against incoming attacks.

7. Validate the API works when called externally.