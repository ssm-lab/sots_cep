# Architecture
This section explains the major classes, their responsibilities, and how they interact.

---

## Core Schema

### `Event`
- **Purpose**: Defines the contract for all messages in the system.
- **Fields**:
  - `stream_id`: Unique ID of the source stream.
  - `timestamp`: When the value was observed or imputed.
  - `datatype` / `unit`: Contextual metadata.
  - `value`: field for downstream processing.
  - `observed_value` / `imputed_value`: Provenance of the measurement.
  - `method`: Which predictor was used (`observed`, `kalman`, etc.).
  - `confidence`: Certainty of the value (1.0 for observed, <1.0 for imputed).
  - `extras`: Optional pass-through dict (e.g., `ground_truth` for simulations).

---

## Messaging Layer

### `Server`
- **Purpose**: Central hub that routes events between producers and consumers.
- **Responsibilities**:
  - Maintains three ZeroMQ sockets:
    - ROUTER/DEALER for snapshots.
    - PUB/SUB for broadcasting events.
    - PULL/PUSH for collecting client updates.
  - Stores recent messages in memory for new clients.

### `Client`
- **Purpose**: Generic wrapper around ZeroMQ sockets.
- **Responsibilities**:
  - Subscribes to topics.
  - Publishes events to the bus.
  - Polls for incoming messages.
- **Note**: Extended by `StreamClient`.

---

## Event Stream Layer
  ### `EventStream`
- **Purpose**: Partitions the event bus and places events into their appropriate category so consumers can filter what messages they receive.  

- **Responsibilities**:
  - Maintains partitions (`observed`, `imputed`, `cep`).
  - Publishes events into the correct partition.
  - Registers subscribers so components only receive relevant messages.
  - Dispatches incoming messages from ZeroMQ to the appropriate consumers.
  - Supports graceful shutdown of the pipeline.


#### Partitions

- **Observed Partition (`observed`)**
  - Holds original data directly from streams (simulated or real).
  - May contain missing values (`value=None`), which downstream components (like imputers) must handle.

- **Imputed Partition (`imputed`)**
  - Holds events with added information by predictors (e.g., Kalman filter).
  - Each event has fields like `imputed_value`, `confidence`, and `method` to describe details of each prediction.
  - When the observed data is NaN, the predicted value can be used


- **CEP Partition (`matched`)**
  - Holds events that have passed through the CEP engine and are annotated with details on patterns matched to that event


### `StreamClient`
- **Purpose**: wrapper on client made for the EventStream 
- **Responsibilities**:
  - Each partition (observed, imputed, filtered) owns its own `StreamClient`.
  - Handles ZeroMQ subscription filters (`prefix.stream_id`).
  - Dispatches events to registered consumers.

---

## Stream Layer

### `Stream` (abstract)
- **Purpose**: Defines the interface for all event sources.
- **Responsibilities**:
  - `start(event_stream)`: Begin producing events.
  - `stop()`: shutsdown.
  - Ensures all streams produce events conforming to the `Event` schema.

### `SimulatedStream`
- **Purpose**: Concrete `Stream` implementation for simulation.
- **Responsibilities**:
  - Generates random values with occasional missing data (`None`).
  - Publishes events into the `observed` partition.
  - Attaches ground truth into `extras` for evaluation.

### `StreamManager`
- **Purpose**: Initializes and manages all streams.
- **Responsibilities**:
  - Loads stream definitions from `configs/streams.json`.
  - Starts each configured stream automatically.

---

## Imputation Layer

### `Imputer`
- **Purpose**: appends to events from the observed partition
- **Responsibilities**:
  - Consumes observed events.
  - Predicts missing values using predictor.
  - Publishes enriched events to the `imputed` partition.

  ### `BasePredictor` (abstract)
- **Purpose**: Interface for prediction/imputation algorithms.
- **Responsibilities**:
  - `predict()`: Estimate the next value.
  - `update(observed)`: Adjust with real observation.
  - `confidence()`: Estimate reliability of the prediction.

### `KalmanFilter`
- **Purpose**: Implements a Kalman filter predictor.
- **Responsibilities**:
  - Maintains state (value, rate, acceleration).
  - Computes predictions and updates state with measurements.
  - Provides confidence from state covariance.

### `ImputerManager`
- **Purpose**: Coordinates multiple imputers.
- **Responsibilities**:
  - Initializes imputers for each stream
  - Subscribes them to their observed partitions.

---

## Evaluation & Logging Layer

### `Logger`
- **Purpose**: Unified logger across all partitions.
- **Responsibilities**:
  - Subscribes to all partitions.
  - Writes events to a CSV
  - Used later for offline evaluation.

---

## High-Level Flow
1. **Simulated Stream** produce observed events.
2. **EventStream** routes them into the observed partition.
3. **Imputers** consume observed events, impute missing values, and publish to the imputed partition.
4. **CEP** consumes from imputed, publish to matched
5. **Logger** captures all events (observed, imputed, filtered).
