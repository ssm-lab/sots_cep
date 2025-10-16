# Getting Started  

This section explains how to quickly run the demo and how to plug in your own architectures into the framework.  

---

## 1. Setup

Activate a virtual environment (Recommended to prevent conflicts)
-  Create and activate a Python virtual environment:
  ```bash
  python -m venv venv
  ```
- Activate the virtual environment
  ```bash
  source venv/bin/activate   # On Linux/Mac
  venv\Scripts\activate      # On Windows
  ```
  
Install Dependancies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```  

To run the default Esper CEP engine, you need:

Java 21 (set via maven-compiler-plugin in the build configuration).
Maven 3.6+ (to build and package the JAR with dependencies).

Build the Java layer:
cd app/java
mvn clean package


This produces a self-contained JAR under:
app/java/target/sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar

---

## 2. Run the Demo  

The framework uses a Python Orchestrator as the central entry point. You can find the demo configuration file at `app_examples/main_example/Main.py`.

```python
from app.Orchestrator import Orchestrator
from app.core.cep.cep_engine_types.EsperCEPEngine import EsperCEPEngine

def main():
    orch = Orchestrator(
        pattern_file="patterns/main_example_patterns.json",
        log_dir="data/logs/main_example",
        streams_cfg="app_examples/main_example/configs/streams.json",
        predictors_cfg="app_examples/main_example/configs/predictors.json",
        base_run_name="run",
        cep_engine_cls=EsperCEPEngine,
        cep_engine_kwargs={
            "jar_name": "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
            "java_dir": "app/java",
            "rebuild": True
        }
    )
    orch.start()
```

Then from the project root run the demo using the command:  

```bash
python -m app_examples.main_example.Main
```  

This will:  
- Launch the ZMQ server (default communication layer).  
- Start the Esper CEP engine.  
- Register example streams (speed, engine-temp, fuel).  
- Log all observed/reconstructed events to `data/logs/`.  

---
## 3. CEP Engine and Bridge Overview

The CEP Engine (Complex Event Processing) layer runs in Java (Esper) and is responsible for detecting atomic and complex patterns from reconstructed event streams. It subscribes only to the reconstructed partition, ensuring the engine operates on complete, confidence-annotated data.

The connection between Python and Java is handled by the Bridge (app/core/bridge/JavaCEPBridge): Starts and monitors the Java CEP process using JavaRunner.

The CEP layer is fully modular: The Esper engine can be replaced with another CEP backend (e.g., Siddhi, Drools Fusion) by subclassing CEPEngine and implementing start, stop, and load_patterns. The bridge remains the same regardless of the engine used, maintaining the same communication protocol.

#### Pattern Definitions

Patterns are defined declaratively under: `app/java/src/main/resources/patterns/`

Each file defines rules in EPL (Event Pattern Language) that describe event relationships and detection logic.
These can be edited, added, or replaced without modifying the Python layer

---

## 4. Add a New Stream  

Streams are defined in JSON configs under `app_examples/<example>/configs/streams.json`.  

Each stream entry must include:  

```json
  {
    "speed-2": {
    "datatype": "float",
    "unit": "km/h",
    "interval": 1.0,
    "type": "simulated",
    "params": {
      "min": 10,
      "max": 30
    },
    "predictor_template": "kf1"
  }
}
```  
 
- `datatype` / `unit`: Metadata for the event schema.  
- `interval`: Emission rate in seconds.  
- `type`: Which event generator type class to use.  
- `params`: Arguments passed into the generator.  
- `predictor_template`: Tells the Coordinator which predictor configuration to use when reconstructing missing events for this stream.

Each key in the JSON is the stream ID, mapped to its configuration object

The predictor_template value corresponds to a named entry in your predictors.json config, which defines what type of predictor (e.g., Kalman filter, particle filter) and its parameters should be used for this stream.

After editing, restart the orchestrator:  

```bash
python -m app_examples.main_example.Main
```  

---

## 5. Plug in Your Own Stream  

Sometimes you’ll want different types of streams: simulated, dataset-driven, or real sensors.  

### A. Simulated Stream  

Create a new type under `app/core/stream/stream_types` and register it using the decorator:  

```python
from app.core.stream.Stream import Stream

@register_stream_type("random_walk")
class RandomWalkStream(Stream):
    def __init__(self, stream_id, unit="unit", datatype="float", interval=5, params={}):
        super().__init__(stream_id, datatype, unit, interval, params)
        ....

    def generate_event(self):
        ...
      )
```  

Then reference it in `streams.json`:  

```json
{
  "sim-1" :{
    "datatype": "float",
    "unit": "value",
    "interval": 1.0,
    "type": "random_walk",
    "params": { "start": 10 },
    "predictor_template": "kf1"
  }
}
```  


---

## 6. Define Predictors  

Predictors are configured in `app_examples/<example>/configs/predictors.json`.  

These define which predictors are available, their type, and any initialization parameters.  
Streams reference them by name through the **`predictor_template`** field.  

```json
{
  "kf1": {
    "type": "KalmanPredictor",
    "params": {
      "initial_variance": 1.0,
      "process_noise": 0.01,
      "measurement_noise": 0.1
    }
  },
  "kf2": {
    "type": "KalmanPredictor",
    "params": {
      "initial_variance": 2.0,
      "process_noise": 0.05,
      "measurement_noise": 0.2
    }
  }
}

```  
Here kf1, kf2 are templates (referenced by streams in streams.json).

Each template specifies the predictor type and its params.

---

## 7. Add Your Own Predictor  

Predictors define how missing values are estimated when streams drop events.

To add a new one, create a class under app/core/reconstruction/predictor_types and register it using the decorator:

```python
from .BasePredictor import BasePredictor
from ..PredictorRegistry import register_predictor

@register_predictor("mypredictor")
class MyPredictor(BasePredictor):
    def __init__(self, **kwargs):
        super().__init__(name="MyPredictor")

    def update(self, value):
        pass

    def predict(self):
        return 0.0

    def confidence(self):
        return 0.5
```  

Then reference in `predictors.json`:  

```json
{
  "mypredictor_template":{
    "type": "mypredictor",
    "params": { "alpha": 0.9 }
  }
}
```  

Finally, point a stream to it in streams.json:
```json
{
  "fuel-1": {
    "type": "simulated",
    "unit": "%",
    "datatype": "float",
    "interval": 5.0,
    "params": {
      "min_value": 0.0,
      "max_value": 100.0,
      "start_value": 50.0,
      "drift": -0.2,
      "noise": 0.1,
      "drop_chance": 0.05
    },
    "predictor_template": "mypredictor_template"
  }
}
```  
---

## 8. Plug in a New Communication Layer  

1. Implement `Client` (publish/subscribe/dispatch).  
2. Implement `Server` (run/stop/cleanup).  
3. Point orchestrator at them:  

```python
orch = Orchestrator(
    ...,
    client_type=MyKafkaClient,
    server_type=MyKafkaServer
)
```  

---

## 9. Plug in a New CEP Engine  

1. Subclass `CEPEngine` and implement `start`, `stop` 
2. Provide it to orchestrator:  

```python
orch = Orchestrator(
    ...,
    cep_engine_cls=MyCustomEngine,
    cep_engine_kwargs={"patterns": "patterns/custom.json"}
)
```  

---

## 9. Where to Look Next  

- **Logs**: Stored under `data/logs/<example>_<timestamp>/`.  
- **Patterns**: JSON definitions in `app/java/src/main/resources/patterns/*.json`.  

---

With this, you can run the demo as-is, or extend it with your own streams (simulated, dataset, or real sensors), predictors, communication layers, and CEP engines.  
