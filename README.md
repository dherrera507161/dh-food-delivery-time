# dh-food-delivery-time
This repo is dedicated for an imaginary food delivery company as a part of a job interview problem. The main task is to investigate the main blockers affecting the timely delivery of goods, build a system to predict delivery time, and share actionable insights that help the Ops team respond more intelligently. As such, the repo is divided in four folders:
1. SQL queries to identify the main problems.
2. The main prediction model
3. Draft of how an API data extraction would look like
4. Future next steps

## Setting Up & Running This Project

- **SQL** (`sql/`): queries use DuckDB, which lets you `FROM file.csv` directly (`pip install duckdb` to run them, then `duckdb < sql_tests.sql` from inside `sql/`). To use another engine, `CREATE TABLE` from each CSV and swap the `FROM <file>.csv` references for the table names.

- **Model pipeline results**: If you just wish to read the data generated, feel free the read the files directly from the data folder in /workspaces/dh-food-delivery-time/model_pipeline/data.
- **Run the model pipeline yourself**
To check the code runs properly, run the code in your terminal, ensuring the terminal points to /workspaces/dh-food-delivery-time/:
  ```bash
  cd model_pipeline
  pip install -r requirements.txt
  kedro run
  ```
