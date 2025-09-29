# Uncertainty-Aware Stream Processing for Systems of Digital Twins

## Project Overview
This framework provides a modular event processing pipeline for systems of digital twins contexts. It integrates real-time data streams, missing data reconstruction with uncertainty estimates, and Complex Event Processing (CEP) to enable reliability-aware situational awareness.

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

## Documentation

## Extensibility
- Replace ZeroMQ with any messaging layer (Kafka, RabbitMQ).
- Swap out Esper CEP with other CEP engines or custom rule evaluators.
- Add new predictors or stream types by extending base classes.
- Subscribe external systems (dashboards, loggers) to partitions without changing the core pipeline.

## Example Workflow
- Simulated stream generate observed data (with occasional dropouts).
- Imputers consume observed events → predict missing values → publish enhanced events.
- GlobalLogger subscribes to all partitions → writes structured CSV logs.
- Evaluation computes MAE, RMSE, R² against embedded ground truth.
