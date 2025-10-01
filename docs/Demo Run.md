# Example Run (Main Example)  
To demonstrate the pipeline, we provide a demo that ties all components together. Located in app_examples/main_example

## Demo Scenario  
The `main_example` demo simulates a **vehicle digital twin** with three core data streams:  

- **Speed (`speed-1`)**: Simulated vehicle speed in arbitrary units.  
- **Engine Temperature (`engine-temp-1`)**: Simulated thermal state of the engine.  
- **Fuel Level (`fuel-1`)**: Simulated remaining fuel percentage.  

These streams are subject to dropouts and reconstructions, then fed into the CEP engine to detect meaningful patterns about the vehicle’s operational state.  

---

## Patterns Tracked  

The CEP engine listens to the **reconstructed partition** and continuously evaluates the following patterns:  

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
- **Streams Settings**: `app_examples/main_example/configs/streams.json`  
- **Filters Settings**: `app_examples/main_example/configs/filters.json`  
- **Logs**: Written to `data/logs/main_example/` with a timestamped subfolder.  

---

## Expected Flow  

### 1. Startup  
- The **Orchestrator** launches the ZMQ server, CEP engine (Esper by default), logger, and coordinator.  
- Each stream is registered and scheduled.  

### 2. Event Generation  
- Example streams (e.g., `speed`, `engine-temp`) begin producing events at fixed intervals.  
- Events are routed into the **observed** partition.  

### 3. Reconstruction  
- When a stream does not emit a scheduled event, the **Coordinator** invokes its reconstructor.  
- The **Reconstructor** uses a predictor (e.g., **Kalman filter**) to impute the value and generates a confidence score.  
- Both observed and reconstructed events flow into the **reconstructed** partition.  

### 4. CEP Pattern Detection  
- **Esper** listens to the reconstructed partition.  
- When conditions are met (e.g., `WarmEngine` pattern), it emits a match.  

### 5. Logging  
- The **Logger** subscribes to all partitions.  
- Each event is written to CSV for offline evaluation.  