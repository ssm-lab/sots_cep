# Example Run (Main Example)  
To demonstrate the complete pipeline, we provide a self-contained demo located in `app_examples/main_example`. The demo is executed through the **Orchestrator**, which assembles and manages all components automatically.

---

## Demo Scenario  
The `main_example` demo simulates a **vehicle digital twin** with three simulated event sources:  

- **Speed (`speed-1`)**: Simulated vehicle speed in arbitrary units.  
- **Engine Temperature (`engine-temp-1`)**: Simulated thermal state of the engine.  
- **Fuel Level (`fuel-1`)**: Simulated remaining fuel percentage.  

Each source emits events at its own configured interval and may experience intermittent dropouts. When observations are missing, reconstructed events are generated and re-inserted into the event stream with associated confidence metadata. All events, observed and reconstructed, are then processed uniformly by the CEP engine.

---

## Patterns Tracked  

The CEP engine listens to the event stream and continuously evaluates the following patterns:  

### Atomic Patterns  
- **Overspeeding**: Speed exceeds 25.  
- **EngineOverheat**: Engine temperature exceeds 28.  
- **LowFuel**: Fuel drops below 15.5.  
- **NormalCruise**: Speed between 15–25 (safe operating zone).  
- **WarmEngine**: Engine temperature between 24–28.  

### Temporal / Composite Patterns  
- **HighSpeedOverheat**: A high-speed event (>20) followed by engine overheat (>27).  
- **CriticalCondition**: Sequence of high speed → engine overheat → low fuel (compound failure).  
- **GradualFuelDrop**: Successive events showing decreasing fuel.  
- **StopAndGo**: Speed dips below 16 (stop) followed by exceeding 20 (go).  
- **SpeedOscillation**: Rapid acceleration (>22) followed by sharp braking (<18).  
- **OverheatCooldown**: Overheat event (>28) followed by cooldown (<25).  

---


### Run Command  
```python app_examples/main_example/Main.py```

---
## Configuration Used  

- **Patterns**: `patterns/main_example_patterns.json`  
- **Event sources Settings**: `app_examples/main_example/configs/sources.json`  
- **Predictor Settings**: `app_examples/main_example/configs/predictors.json`  
- **Config Settings**: `app_examples/main_example/configs/config.json` 
- **Logs**: Written to `data/logs/main_example/demo_run` with a timestamped subfolder.  

---

## Expected Flow  

### 1. Startup  
- The Orchestrator loads all configuration files.
Messaging infrastructure (ZMQ server and clients) is started.
The CEP engine (Esper) is launched.
The event stream, coordinator, and logger are initialized.
Event sources are dynamically constructed and scheduled.

### 2. Event Generation  
- Example event sources (e.g., `speed`, `engine-temp`) begin producing events at configured intervals.  
- Events are published into the EventStream with status = observed..  

### 3. Reconstruction  
- When a event source does not emit a scheduled event, the **Coordinator** invokes its reconstructor.  
- The **Reconstructor** uses a predictor (e.g., **Kalman filter**) to impute the value and generates a confidence score.  
- A reconstructed event is emitted back into the EventStream with status = reconstructed

### 4. CEP Pattern Detection  
- **Esper** listens to the reconstructed partition.  
- When conditions are met (e.g., `WarmEngine` pattern), it emits a match.  

### 5. Logging  
- The **Logger** subscribes to all partitions.  
- Each event is written to CSV for offline evaluation.  