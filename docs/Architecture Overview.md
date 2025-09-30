# Architecture Overview
This section explains the core classes and their responsibilities.

---
## CEP Layer
### `app/core/cep/`
#### CEPEngine (Abstract)
- **Purpose**: Abstracts the Complex Event Processing backend.  
- **Role**: Wraps the lifecycle of an external CEP engine (e.g., Esper) or a custom implementation.  
- **Features**:
  - Neutral interface (`start`, `stop`) for plugging in different CEP engines.
  - Loads patterns and configurations dynamically.  
- **Design Choice**: Keeps the framework agnostic to a specific CEP backend.  

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

---
## Utils
### `app/core/utils/`
#### JavaRunner
- **Purpose**: Utility for running Java-based CEP engines.  
- **Role**: Starts/stops Esper or other Java processes.  
- **Features**:
  - `start_java()` → launch process with args.  
  - `stop_java()` → clean shutdown.  
- **Design Choice**: Bridges Python orchestration with Java CEP runtime.

#### Logger (Abstract)
- **Purpose**: Event consumer that logs events to disk.  
- **Role**: Subscribes to partitions in the `EventStream` and writes events into structured files (e.g. CSV, text).  
- **Features**:
  - Creates a log file per partition.  
  - Automatically appends new events with consistent schema.  
  - Useful for offline evaluation, debugging, and reproducibility.  
- **Design Choice**: Keeps logs decoupled from the runtime so experiments can be replayed and analyzed later.  


