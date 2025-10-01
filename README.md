# Uncertainty-Aware Stream Processing for Systems of Twinned Systems

## Repository Structure

- `/app` – Core project code
  - `/core` – Main Python modules
    - `/cep` – CEP engine abstraction
    - `/communication` – Server/Client communication abstractions
    - `/reconstruction` – Reconstructors for handling missing/incomplete data streams
    - `/runtime` – Coordinator, event dispatch, and execution logic
    - `/schema` – Shared event schema definitions
    - `/stream` – Data stream sources (simulated or dataset-based)
    - `/utils` – Utility functions and helpers
  - `/java` – Java integration layer (Esper connection and orchestration)
  - `Orchestrator.py` – Entry point for launching the full pipeline (Esper, server, streams, logging)
- `/app_examples` – Example pipelines and demos
- `/assets` – Static assets
- `/data` – Logs, evaluation results, and datasets
- `/docs` – Documentation
- `/tests` – Unit tests
