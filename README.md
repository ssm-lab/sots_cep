# Uncertainty-Aware Stream Processing for Systems of Digital Twins
![Unit tests](https://github.com/faith176/sots_kalman_filters/actions/workflows/unit-tests.yml/badge.svg?branch=master)

## Project Overview
This framework implements an pipeline for simulating, imputing, and processing data streams. It’s designed to support runtime data reliability in complex event processing (CEP) for systems of twinned systems.


Update project requirements.txt with <pipreqs . --force> at root folder

## Repository Structure
- `/app` – Core project code
  - `/configs` – JSON configs for filters and streams
  - `/data` – Logs and evaluation results from runs
  - `/imputation` – Imputation logic and predictors
  - `/messaging` – EventStream + ZeroMQ server/client
  - `/schema` – Shared event schema definition
  - `/streams` – Data stream sources (simulated, todo - dataset-based)
- `/app_examples` – Example pipelines
- `/tests` – Unit tests


## Project Structure
- Clone this repository.
- Install requirements via `pip install -r requirements.txt`.
- Start the event pipeline `python -m app_examples/Main.py`.
- Stop with Ctrl+C (logger will close and save the CSV)
- Evaluate results: python app_examples/Main_Evaluation.py


## Example Workflow
- Simulated stream generate observed data (with occasional dropouts).
- Imputers consume observed events → predict missing values → publish enhanced events.
- GlobalLogger subscribes to all partitions → writes structured CSV logs.
- Evaluation computes MAE, RMSE, R² against embedded ground truth.
