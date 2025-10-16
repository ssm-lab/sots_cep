# Architecture Overview
This section explains the core classes and their responsibilities.

---
## Bridge Layer
### `app/core/bridge/`
#### JavaCEPBridge
- **Purpose**: Manages inter-process communication and lifecycle control between the Python orchestration layer and the Java CEP engine (Esper).  
- **Role**: Acts as a bridge that sends reconstructed events to Java 
- **Features**:
  - Launches and monitors the Java CEP process using `JavaRunner`.  
  - Exchanges data asynchronously via ZeroMQ PUB/SUB sockets.  
- **Design Choice**: Bridges components of the two programming languages
---
## Communication Layer
### `app/core/communication/`
#### Client (Abstract)
- **Purpose**: Messaging client for publish/subscribe.  
- **Role**: Represents how a single participant communicates with the event bus.  
- **Features**:
  - `publish(event, stream_id)` → sends events.
  - `subscribe_to(stream_id, consumer)` → registers consumers.
  - `dispatch()` → delivers incoming events.  
- **Design Choice**: Abstract, so implementations can use ZMQ, Kafka, MQTT, etc.

#### Server (Abstract)
- **Purpose**: Messaging server that forwards events between clients.  
- **Role**: Central message broker (e.g., ZMQ PUB/SUB).  
- **Features**:
  - Lifecycle methods (`run`, `stop`, `_cleanup`).
  - Threaded or blocking modes for flexibility.  
- **Design Choice**: Abstract base so multiple messaging backends can be supported.

---
## Runtime Layer
### `app/core/runtime/`
#### Coordinator
- **Purpose**: High-level orchestrator of streams, reconstructors, and predictors.  
- **Role**: Config-driven manager that sets up the pipeline.  
- **Features**:
  - Builds event streams from configs.  
  - Starts/stops reconstructors and generators.  
  - Handles threading and scheduling.  
- **Design Choice**: Handles initialization of events and core classes

#### EventStream
- **Purpose**: Core event bus abstraction.  
- **Role**: Manages partitions (e.g. `observed`, `reconstructed`) and routes events.  
- **Features**:
  - `add_event()` → injects an event into a partition.  
  - `subscribe()` → attach consumers to partitions/streams.  
  - `dispatch()` → runs the delivery loop.  
- **Design Choice**: Partitioning ensures clean separation of event lifecycles.

#### EventConsumer (Interface)
- **Purpose**: Abstract base for anything that processes events.  
- **Role**: Used by loggers, UIs, reconstructors, monitors.  
- **Features**:
  - `consume_event(event)` → common entry point for all consumers.  
- **Design Choice**: Guarantees a uniform contract across the framework.

#### EventGenerator (Interface)
- **Purpose**: Produces events from simulation or datasets.  
- **Role**: Defines the raw source of events before any imputation.  
- **Features**:
  - `generate_event(ts)` → returns a new event dict.  
- **Design Choice**: Supports use with simulated data, dataset data, and real eventstreams

---
## Stream Layer
### `app/core/stream/`
#### Stream
- **Purpose**: Defines a single logical stream.  
- **Role**: Provides data from one source (sensor, dataset, synthetic).  
- **Features**:
  - `generate_event()` → produces events on demand.  
- **Design Choice**: Keeps each sensor/source modular. 

---
## Reconstruction Layer
### `app/core/reconstruction/`
#### Reconstructor
- **Purpose**: Handles missing events.  
- **Role**: Uses predictors to reconstruct gaps.  
- **Features**:
  - Delegates to a `Predictor` for imputation.  
  - Adds metadata like `confidence`, `method`, `reconstruction_flag`.  
- **Design Choice**: Keeps gap-filling logic separate from routing.

#### Predictor (Abstract)
- **Purpose**: Encapsulates forecasting/imputation algorithms.  
- **Role**: Provides predicted values with uncertainty.  
- **Features**:
  - `predict()` → return next value.  
  - `update()` → update internal state.  
  - `confidence()` → expose uncertainty.  
- **Examples**: Kalman Filter, Particle Filter.  
- **Design Choice**: Native uncertainty support for CEP integration.  


---
## CEP Layer
### `app/java/src/main/java/cep/`
#### CEPEngine (Abstract)
- **Purpose**: Abstracts the Complex Event Processing (CEP) backend.  
- **Role**: Manages the lifecycle of a CEP engine such as Esper or a custom implementation, enabling detection of atomic and complex events.  
- **Features**:
  - Unified interface (`start`, `stop`, `load_patterns`) for integrating different CEP engines.  
  - Dynamically loads and registers **event patterns** from configuration (EPL, JSON, or other declarative formats).  
  - Manages subscriptions for **atomic events** (e.g., sensor-level triggers) and **complex events** (compositions of multiple atomic or complex patterns).  
  - Supports hierarchical rule evaluation, allowing high-level system alerts to emerge from lower-level detections.  
- **Design Choice**: Keeps the pipeline agnostic to a specific CEP backend


---
## Schema
### `app/core/schema/`
#### Event
- **Purpose**: Canonical structure for all messages.  
- **Responsibilities**:
  - Provide a consistent schema for all events in the pipeline.
  - Carry provenance (`origin`, `status`) and reliability (`confidence`, `reconstruction_flag`).
- **Fields**:  
  - `stream_id`: Source identifier.  
  - `event_ts` / `sampled_ts` / `arrival_ts`: Timing metadata.  
  - `datatype` / `unit`: Context.  
  - `value`: The primary signal (observed or imputed).  
  - `reconstructed_value`: Predictor’s estimate.  
  - `reconstruction_flag`: `True` if the value was imputed.  
  - `reconstruction_method`: Which predictor was used.  
  - `confidence`: Certainty score.  
  - `origin` / `status`: Provenance markers (`observed`, `reconstructed`, `missing`).  
  - `extras`: Optional metadata for ground truth or annotations.  

### `app/java/src/main/java/schema/pattern`
#### Pattern
- **Purpose**: Canonical representation of an event pattern (atomic or complex) detected by the CEP engine.  
- **Responsibilities**:  
  - Provide a consistent schema for all events in the pipeline. 
  - Maintain hierarchical structure, allowing multi-level compositions (complex patterns made of atomic or other complex subpatterns).  

- **Fields**:  
  - `pattern_name`: Identifier of the pattern.  
  - `pattern_type`: Type of pattern — `"atomic"` or `"complex"`.  
  - `confidence`: Numeric confidence score  
  - `stream_id`: Representative stream identifier (used for joins).  
  - `stream_ids`: Set of all contributing stream identifiers for this pattern (traceability).  
  - `events_nested`: List of event groups that contributed to the pattern; each sublist corresponds to one subpattern’s matched events.  

- **Design Choice**:  
  - Provides a consistent abstraction for both atomic and complex detections

---
## Utils
### `app/core/utils/`
#### Logger (Abstract)
- **Purpose**: Event consumer that logs events to disk.  
- **Role**: Subscribes to partitions in the `EventStream` and writes events into structured files (e.g. CSV, text).  
- **Features**:
  - Creates a log file per partition.  
  - Automatically appends new events with consistent schema.  
  - Useful for offline evaluation, debugging, and reproducibility.  
- **Design Choice**: Keeps logs decoupled from the runtime so experiments can be replayed and analyzed later.  


