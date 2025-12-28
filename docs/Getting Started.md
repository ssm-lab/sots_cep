# Getting Started  

This section explains how to run the framework using the configuration-driven **Orchestrator** and how to customize the pipeline by modifying declarative configuration files.

---

## 1. Setup

It is recommended to use a Python virtual environment to avoid dependency conflicts.

Create a virtual environment:
```bash
python -m venv venv
```

Activate the environment:
```bash
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Java Requirements

The default CEP backend uses **Esper**, which runs in Java. To build and run the Java layer, you need:

- **Java 21** (as specified by the Maven compiler plugin)
- **Maven 3.6+**

Build the Java CEP module:
```bash
cd app/java
mvn clean package
```

This produces a self-contained JAR at:
```
app/java/target/sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar
```

---

## 2. Running the Demo

The system is started through the Python **Orchestrator**, which constructs the entire pipeline from configuration files.  
A complete example is provided under:

```
app_examples/main_example/
```

The entry point is `Main.py`:

```python
from app.Orchestrator import Orchestrator

def main():
    orch = Orchestrator(
        config_path="app_examples/main_example/configs/config.json"
    )
    orch.start()

if __name__ == "__main__":
    main()
```

Run the demo from the project root:
```bash
python -m app_examples.main_example.Main
```

This will:

- Start the messaging server (ZeroMQ by default)
- Launch the Java-based CEP engine
- Instantiate all event sources from configuration
- Initialize the coordinator and reconstruction pipeline
- Log all observed and reconstructed events

---

## 3. Orchestrator Overview

The **Orchestrator** is the central entry point of the framework. It is responsible for assembling, starting, and stopping all components.

All runtime behavior is defined declaratively in a single configuration file. The orchestrator performs the following steps:

1. Starts the messaging server and event stream
2. Launches the CEP engine (if enabled)
3. Registers loggers as passive observers
4. Initializes the coordinator and reconstruction logic
5. Dynamically constructs and starts event sources
6. Manages graceful shutdown of all components

This design ensures reproducibility and allows experiments to be re-run by sharing configuration files alone.

---

## 4. Configuration Structure

The orchestrator expects a JSON configuration file with the following sections:

- **messaging** – communication backend and endpoints
- **logging** – logging behavior and output directory
- **sources_config** – path to source definitions
- **coordination** – predictor configuration
- **cep** – CEP engine configuration

Example (abridged):

```json
{
  "messaging": {
    "server_type": "zmq",
    "client_type": "zmq",
    "pub_endpoint": "tcp://*:5557",
    "pull_endpoint": "tcp://*:5558"
  },
  "logging": {
    "enabled": true,
    "base_dir": "data/logs/main_example"
  },
  "sources_config": "app_examples/main_example/configs/sources.json",
  "coordination": {
    "predictors_config": "app_examples/main_example/configs/predictors.json"
  },
  "cep": {
    "enabled": true,
    "pattern_cfg": "patterns/main_example_patterns.json",
    "jar_name": "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
    "java_dir": "app/java",
    "rebuild": true,
    "log_matches": true
  }
}
```

---

## 5. Defining Event Sources

Event sources are defined in a separate JSON file to encourage reuse across experiments.

Example `sources.json`:
```json
{
  "speed-1": {
    "type": "simulated",
    "datatype": "float",
    "unit": "km/h",
    "interval": 1.0,
    "params": {
      "min": 0.0,
      "max": 160.0,
      "start_value": 20.0,
      "drift": 2.0,
      "noise": 4.0,
      "drop_chance": 0.15
    },
    "predictor_template": "kf_fast"
  }
}
```

Each entry defines:

- **type**: which source class to instantiate
- **interval**: expected emission period
- **params**: constructor arguments for the source
- **predictor_template**: which predictor to use for reconstruction

Sources are instantiated dynamically via a registry, allowing new source types to be added without modifying the orchestrator.

---

## 6. Defining Predictors

Predictors are configured separately and referenced by name.

Example `predictors.json`:
```json
{
  "kf_fast": {
    "type": "KalmanFilter",
    "params": {
      "dt": 0.1,
      "Q": 0.1,
      "R": 0.2
    }
  }
}
```

Each predictor template specifies:

- The predictor implementation
- Initialization parameters

The coordinator uses these templates to construct predictors for each source.

---

## 7. Adding Custom Sources or Predictors

New sources and predictors can be added by:

1. Implementing the corresponding abstract base class
2. Registering the implementation in the appropriate registry
3. Referencing the new type by name in the configuration

---

## 8. CEP Engine Integration

The CEP layer runs in Java and evaluates atomic and complex event patterns over the reconstructed event stream.

Patterns are defined declaratively in JSON and expressed using Esper EPL.  
They can be modified independently of the Python orchestration logic.

Alternative CEP engines can be integrated by implementing the `CEPEngine` interface or updated `EventProcessor` and updating the configuration.

---

## 9. Logs and Outputs

All events and detected patterns are logged under:
```
data/logs/<example>/<timestamp>/
```

These logs can be used for offline evaluation, debugging, and reproducibility.

---


## 10. Where to Look Next  

- **Logs**: Stored under `data/logs/<example>_<timestamp>/`.  
- **Patterns**: JSON definitions in `app/java/src/main/resources/patterns/*.json`.  

---

With this, you can run the demo as-is, or extend it with your own configurations.  
