# Getting Started  

This section explains how to quickly run the demo and how to plug in your own architectures into the framework.  

---

## 1. Install Dependencies  

```bash
pip install -r requirements.txt
```  

Ensure **Java 11+** is installed if you plan to run the default **Esper CEP** engine.  

---

## 2. Run the Demo  

From the project root:  

```bash
python -m app_examples.main_example.Main
```  

This will:  
- Launch the **ZMQ server** (default communication layer).  
- Start the **Esper CEP engine**.  
- Register example streams (speed, engine-temp, fuel).  
- Log all observed/reconstructed events to `data/logs/`.  

---

## 3. Add a New Stream  

Streams are defined in JSON configs under `app_examples/<example>/configs/streams.json`.  

Each stream entry must include:  

```json
{
  "id": "speed-2",
  "datatype": "float",
  "unit": "km/h",
  "interval": 1.0,
  "type": "simulated",
  "params": {
    "min": 10,
    "max": 30
  }
}
```  

- `id`: Unique stream identifier.  
- `datatype` / `unit`: Metadata for the event schema.  
- `interval`: Emission rate in seconds.  
- `type`: Which event generator type class to use.  
- `params`: Arguments passed into the generator.  

After editing, restart the orchestrator:  

```bash
python -m app_examples.main_example.Main
```  

---

## 4. Plug in Your Own Stream  

Sometimes you’ll want **different types of streams**: simulated, dataset-driven, or real sensors.  

### A. Simulated Stream  

Create a new type under `app/core/stream/stream_types` and register it using the decorator:  

```python
from app.core.stream.Stream import Stream

@register_stream_type("random_walk")
class RandomWalkStream(Stream):
    def __init__(self, stream_id, datatype="float", unit="unit", **kwargs):
        super().__init__(stream_id, datatype, unit)
        self.value = kwargs.get("start", 0)

    def generate_event(self):
        ...
      )
```  

Then reference it in `streams.json`:  

```json
{
  "id": "sim-1",
  "datatype": "float",
  "unit": "value",
  "interval": 1.0,
  "type": "random_walk",
  "params": { "start": 10 }
}
```  


---

## 5. Define Filters  

Filters are configured in `app_examples/<example>/configs/filters.json`.  

These define which **predictors** to use when values are missing:  

```json
{
  "stream_id": "speed-1",
  "type": "KalmanPredictor",
  "params": {
    "q": 0.01,
    "r": 0.1
    ...
  }
}
```  

---

## 6. Add Your Own Predictor  

Predictors define how missing values are estimated.  

To add a new one create a new type under `app/core/reconstruction/predictor_types` and register it using the decorator:  

```python
from app.core.reconstruction.predictor_types.BasePredictor import BasePredictor

@register_predictor("KalmanFilter")
class MyPredictor(BasePredictor):
    def __init__(self, **kwargs):
        super().__init__()
        self.params = kwargs

    def update(self, value):
        pass

    def predict(self):
        return 0.0

    def confidence(self):
        return 0.5
```  

Then reference in `filters.json`:  

```json
{
  "stream_id": "fuel-1",
  "predictor": "MyPredictor",
  "params": { "alpha": 0.9 }
}
```  

---

## 7. Plug in a New Communication Layer  

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

## 8. Plug in a New CEP Engine  

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

## 9. Templates  

**streams.json**  

```json
[
  {
    "id": "speed-1",
    "datatype": "float",
    "unit": "km/h",
    "interval": 1.0,
    "generator": "SyntheticStream",
    "params": { "min": 10, "max": 30 }
  },
  {
    "id": "engine-temp-1",
    "datatype": "float",
    "unit": "C",
    "interval": 1.0,
    "generator": "SyntheticStream",
    "params": { "min": 20, "max": 30 }
  },
  {
    "id": "fuel-1",
    "datatype": "float",
    "unit": "L",
    "interval": 2.0,
    "generator": "SyntheticStream",
    "params": { "min": 10, "max": 40 }
  }
]
```  

**filters.json**  

```json
[
  {
    "stream_id": "speed-1",
    "predictor": "KalmanPredictor",
    "params": { "q": 0.01, "r": 0.1 }
  },
  {
    "stream_id": "engine-temp-1",
    "predictor": "KalmanPredictor",
    "params": { "q": 0.01, "r": 0.1 }
  },
  {
    "stream_id": "fuel-1",
    "predictor": "MyPredictor",
    "params": { "alpha": 0.9 }
  }
]
```  

---

## 10. Where to Look Next  

- **Logs**: Stored under `data/logs/<example>_<timestamp>/`.  
- **Patterns**: JSON definitions in `patterns/*.json`.  
- **Streams & Filters**: Configurable via `app_examples/<example>/configs/`.  

---

With this, you can run the demo as-is, or extend it with your own streams (simulated, dataset, or real sensors), predictors, communication layers, and CEP engines.  
