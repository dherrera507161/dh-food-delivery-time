# dh-food-delivery-time
This repo is dedicated for an imaginary food delivery company as a part of a job interview problem. The main task is to investigate the main blockers affecting the timely delivery of goods, build a system to predict delivery time, and share actionable insights that help the Ops team respond more intelligently. As such, the repo is divided in four folders:
1. SQL queries to identify the main problems.
2. The main prediction model
3. Draft of how an API data extraction would look like
4. Future next steps

## Setting Up & Running This Project

This repo has two runnable pieces — the SQL analysis in `sql/`, and the Kedro model pipeline in `model_pipeline/` — each with its own setup below.

**Prerequisites:** Python 3.12+, `pip`

### Running the SQL analysis (`sql/`)

The queries in `sql/sql_queries.sql` and `sql/sql_tests.sql` target **DuckDB**, not standard SQL — they query the CSVs in `sql/` directly by filename (e.g. `FROM orders.csv`), which is DuckDB-specific. DuckDB isn't pinned in any `requirements.txt` in this repo, so install it separately:

```bash
pip install duckdb
```

Then, from inside the `sql/` directory (so the relative CSV paths resolve), either:

- Run a file directly with the DuckDB CLI: `duckdb < sql_tests.sql`
- Or open a DuckDB CLI/Python session and run individual queries interactively — how they were originally authored and verified.

Read `sql/sql_insights.md` first: it's the written report — the same exploratory queries embedded alongside the business interpretation of their results — for context before re-running anything.

Useful docs:
- [DuckDB documentation](https://duckdb.org/docs/)
- [DuckDB SQL introduction](https://duckdb.org/docs/sql/introduction)

### Running the model pipeline (`model_pipeline/`)

```bash
cd model_pipeline
pip install -r requirements.txt
kedro run
```

`kedro run` executes the full pipeline end to end: data cleaning, train/test split, feature encoding, training all 5 models, generating predictions, and building every reporting table under `data/08_reporting/`. See [`model_pipeline/docs/source/pipeline_overview.md`](model_pipeline/docs/source/pipeline_overview.md) for what each stage and node does.

To explore the trained models and results visually, launch Jupyter with the Kedro `catalog` pre-loaded:

```bash
kedro jupyter notebook   # or: kedro jupyter lab
```

- `notebooks/model_reporting.ipynb` — predicted vs actual plots, SHAP plots
- `notebooks/hyperparameter_notebook.ipynb` — train vs test error across hyperparameter sweeps
- `notebooks/performance_analysis.ipynb` — predicted vs actual by category, with R2 per facet

To run the test suite:

```bash
pytest                          # everything
pytest -m test_model_quality    # only the data-quality checks (see tests/pipelines/model_pipeline/test_pipeline.py)
```

Useful docs:
- [Kedro documentation](https://docs.kedro.org)
- [Kedro data catalog](https://docs.kedro.org/en/stable/catalog-data/introduction/)
- [pytest documentation](https://docs.pytest.org/en/stable/)
- [pytest markers (`-m`)](https://docs.pytest.org/en/stable/how-to/mark.html)
