# Architecture  

This section explains the core classes, their responsibilities, and how they interact in the pipeline.  

---

## Core Schema  

### `Event`  
- **Purpose**: Canonical structure for all messages.  
- **Fields**:  
  - `stream_id`: Source identifier.  
  - `event_ts` / `sampled_ts` / `arrival_ts`: Timing metadata.  
  - `datatype` / `unit`: Context.  
  - `value`: The primary signal (observed or imputed).  
  - `reconstructed_value`: Predictor’s estimate.  
  - `reconstruction_flag`: `True` if the value was imputed.  
  - `reconstruction_method`: Which predictor was used.  
  - `confidence`: Certainty score (1.0 for observed).  
  - `origin` / `status`: Provenance markers (`observed`, `reconstructed`, `missing`).  
  - `extras`: Optional metadata for ground truth or annotations.  

---

## Runtime Layer  

### `EventStream`  
- **Purpose**: Internal event bus that partitions events.  
- **Responsibilities**:  
  - Organize events into partitions (`observed`, `reconstructed`).  
  - Allow subscribers (loggers, reconstructors, CEP clients) to filter by partition and stream.  
  - Dispatch events to consumers.  

#### Partitions  
- **Observed**: Raw events directly from streams.  
- **Reconstructed**: Continuous timeline (observed copies + imputed values).  

---

### `Coordinator`  
- **Purpose**: Central controller for streams and reconstructors.  
- **Responsibilities**:  
  - Load configs for streams and predictors.  
  - Build and start each stream in its own thread.  
  - Use `TickScheduler` to trigger events at fixed intervals.  
  - Forward timeouts to reconstructors for imputations.   

---

## Stream Layer  

### `Stream` (abstract)  
- **Purpose**: Base interface for data sources.  
- **Responsibilities**:  
  - Define `generate_event()` for producing raw measurements.  
  - Provide metadata (`unit`, `datatype`, `interval`).  


---

## Reconstruction Layer  

### `Reconstructor`  
- **Purpose**: Wraps a predictor to handle missing values.  
- **Responsibilities**:  
  - Subscribe to observed events.  
  - Run `update()` on predictors when real values arrive.  
  - Run `predict()` when handling timeouts (missing events).  
  - Publish processed events to the reconstructed partition.  


### `BasePredictor` (abstract)  
- **Purpose**: Unified interface for forecasting/imputation algorithms.  
- **Responsibilities**:  
  - `predict()`: Estimate the next value when missing.  
  - `update(value)`: Incorporate observed measurements.  
  - `confidence()`: Return uncertainty of the estimate.  

---

## High-Level Flow  

1. **Streams** generate raw sensor data (may drop values).  
2. **Coordinator** schedules streams and routes events into the `observed` partition.  
3. On **timeouts**, Coordinator invokes **Reconstructors** to fill gaps.  
4. **Reconstructed events** (copies + imputations) go into the `reconstructed` partition.  
5. **Esper CEP engine** subscribes to reconstructed events, matches patterns
