# Uncertainty-Aware Stream Processing for Systems of Twinned Systems

## Repository Structure

### Root Layout

- `/app` – Core project code  
  - `/core` – Main Python modules  
    - `/bridge` – Python–Java bridge 
    - `/communication` – ZMQ-based server/client abstractions for message routing  
    - `/reconstruction` – Predictors and reconstructors handling missing or uncertain data  
    - `/runtime` – Coordinator and execution logic  
    - `/schema` – Shared event schemas and serialization logic  
    - `/stream` – Data stream definitions (simulated, reconstructed, or dataset-based)  
    - `/utils` – Logging, configuration, and helper utilities  
  - `/java` – Java integration layer (Esper CEP engine and orchestration)
    - `/src/main/java/app` – Java source code organized into packages:
      - `app ` - Main entry point and application lifecycle logic
      - `runtime` –   execution logic
      - `schema.event` – Event definitions shared with the Python layer via JSON schema  
      - `schema.pattern` – Pattern schema representations  
      - `pattern` – Pattern management classes (pattern loading, registration, and metadata)  
      - `cep` – Core CEP interfaces and engine abstractions  
      - `cep.esper` – Implementation of CEP interfaces using the Esper runtime (event injection, listeners, pattern evaluation)  
      - `communication` – Java-side ZeroMQ clients for event exchange with Python  
      - `utils` – Common helpers for parsing and logging  
    - `/src/main/resources/` – Resource directory containing:
      - `patterns/` – Event Pattern Language (EPL) definitions for Esper
  - `Orchestrator.py` – Main entry point for launching the integrated pipeline (spawns Esper process, configures streams, logging, and bridge communication)

- `/app_examples` – Example pipelines, experiment scripts, and demonstration setups  
- `/assets` – Static assets such as figures or architecture diagrams  
- `/data` – Logs, datasets, and experiment results  
- `/docs` – Documentation and supplementary thesis material  
- `/tests` – Unit and integration tests for Python and Java modules  
