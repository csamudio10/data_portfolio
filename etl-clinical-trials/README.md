# Clinical Trial AE Data Pipeline & Dashboard

End-to-end data engineering project that extracts clinical trial adverse event data, transforms it into relational format, validates integrity, loads into SQL, and visualizes results via an interactive dashboard.

## Features

- ETL pipeline
- Data validation layer
- Relational schema
- Incremental loading
- Streamlit dashboard
- SQL analytics queries

## Tech Stack

Python • Pandas • SQLite • Streamlit • SQL

## Run Pipeline

python src/extract.py
python src/transform.py
python src/validate.py
python src/load.py

## Launch Dashboard

streamlit run app.py

https://cliniical-trials-dashboard.streamlit.app/

## Project Architecture

Raw → Processed → Validated → Database → Dashboard
