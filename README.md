# Zodiac Maritime – Dash KPI Dashboard

This project is a Dash + Plotly implementation scaffold for the Zodiac Maritime take-home exercise.

## Local prerequisites

Use Python 3.11 for local development so the environment matches the current Databricks Apps Python runtime. Install Git and VS Code (or another Python IDE).

## 1. Create the environment

PowerShell:

```powershell
python --version
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use:

```powershell
.venv\Scripts\activate.bat
```

## 2. Add the assessment CSV

Place the supplied `vessel_kpi_reports.csv` in:

```text
data/vessel_kpi_reports.csv
```

The application validates the expected assessment columns and initializes a local SQLite database at `data/zodiac.db` on first run.

## 3. Run locally

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:8050
```

## 4. What is already scaffolded

- Vessel/date/KPI/voyage filters
- Power and Speed Plotly scatter charts
- Plotly point/box/lasso selection driving the detail table
- Editable Power % and Speed % cells
- Negative deviation conditional formatting
- Frontend/backend-style validation layer
- SQLite persistence
- Audit log
- Databricks Apps `app.yaml`

## 5. Assumptions to review before submission

The assessment requires a "sane range" for Power % / Speed % but does not define exact bounds. This scaffold uses 0–200 and documents that as an assumption. Adjust it after reviewing the real dataset.

The table has an internal `row_id` because the brief intentionally includes a duplicate Report_ID. Report_ID remains the business identifier and is what is recorded in the audit log.

## 6. Databricks direction

The take-home asks SQLite to stand in for a Databricks Delta MERGE/UPSERT. For a production version, replace the SQLite data access layer with Databricks SQL Warehouse/Delta access. The current code keeps database access isolated in `database/db.py` to make that substitution easier.

## 7. Deployment outline

1. Test locally.
2. Put the project into a Git repository or Databricks workspace folder.
3. Create/configure a Databricks App.
4. Deploy the project using the Databricks Apps workflow.
5. Keep `app.yaml`, `requirements.txt`, and `app.py` at the project root.
6. Configure resources/secrets separately when connecting to Databricks SQL.

## 8. Project structure

```text
app.py
app.yaml
requirements.txt
README.md
assets/
components/
callbacks/
database/
services/
utils/
data/
```
