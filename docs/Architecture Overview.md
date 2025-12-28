# Architecture Overview

This section describes the core architectural layers, the main classes within each layer, and their responsibilities. The architecture follows an event-driven model in which all information exchange occurs through a shared `EventStream`, enabling loose coupling between data sources, reconstruction logic, and downstream analytics.

---

## Orchestration Layer
### `app/Orchestrator`

#### Orchestrator
- **Purpose**:  
  High-level assembly and lifecycle manager for the entire pipeline.
- **Role**:  
  Constructs, configures, and controls all runtime components from configuration files.
- **Responsibilities**:
  - Load experiment configuration (messaging, sources, predictors, CEP, logging).
  - Instantiate and start the messaging server and event stream.
  - Constructs event sources based on source configuration.
  - Initialize and start the `Coordinator`.
  - Launch and manage the Java-based CEP engine through the `EventProcessor`.
  - Register logging components.

- **Design Choice**:
  - Enables reproducible experiments through configuration-driven execution.
  - Decouples system wiring from component implementations.


## Communication Layer
### `app/core/communication/`

#### Client (Abstract)
- **Purpose**: Abstract messaging endpoint for publish/subscribe communication.
- **Role**: Represents a single participant’s connection to the event bus.
- **Responsibilities**:
  - Publish serialized `Event` objects to the event bus.
  - Subscribe to event topics (by source or wildcard).
  - Dispatch received events to registered consumers.
- **Design Choice**:
  - Abstracted to support multiple messaging backends (ZeroMQ, Kafka, MQTT).
  - Decouples event semantics from transport mechanics.

#### Server (Abstract)
- **Purpose**: Message relay between publishing and subscribing clients.
- **Role**: Acts as a lightweight broker that forwards events between producers and consumers.
- **Responsibilities**:
  - Maintain PUB/SUB and PUSH/PULL socket topology.
  - Relay events and support blocking or threaded execution modes.
- **Design Choice**:
  - Enables language-agnostic communication across Python and Java components.

---

## Runtime Layer
### `app/core/runtime/`

#### EventStream
- **Purpose**: Central event bus abstraction for the system.
- **Role**: The only mechanism by which events are propagated between components.
- **Responsibilities**:
  - Publish events into logical partitions (e.g., `observed`, `reconstructed`).
  - Manage subscriptions of `EventConsumer`s to event streams.
  - Dispatch incoming events to consumers via the underlying messaging client.
- **Design Choice**:
  - Enforces a single, uniform communication path.
  - Prevents direct component-to-component coupling.
  - Enables logging and horizontal scaling without modifying current components.

#### EventConsumer (Interface)
- **Purpose**: Common interface for all components that react to events.
- **Role**: Defines the contract for event-driven processing.
- **Responsibilities**:
  - Consume immutable `Event` objects via `consume_event(event)`.
- **Design Choice**:
  - Ensures uniform handling across reconstructors, loggers, coordinators, and CEP adapters.

#### Coordinator
- **Purpose**: Detects absence of expected events and triggers reconstruction when required.
- **Role**: Reasons about deadlines and schedules of event sources.
- **Responsibilities**:
  - Maintain per-source expected schedules derived from configuration.
  - Observe incoming events to detec missed deadlines.
  - Notify the corresponding `Reconstructor` when an event is missing.
- **Design Choice**:
  - Separation of concerns: timing logic is isolated from prediction logic.
  - Avoids embedding scheduling logic inside sources or predictors.

---

## Event Source Layer
### `app/core/source/`

#### EventSource
- **Purpose**: Abstract representation of an event-producing entity.
- **Role**: Origin of observed events (sensors, datasets, simulators).
- **Responsibilities**:
  - Allow user-defined push or pull semantics.
  - Converts observations into the event schema and pushes them onto the event stream.
- **Design Choice**:
  - Keeps data acquisition independent of absence handling.

---

## Reconstruction Layer
### `app/core/reconstruction/`

#### Reconstructor
- **Purpose**: Reconstructs missing events in the event stream.
- **Role**: Creates replacement events using statistical inference.
- **Responsibilities**:
  - Maintain predictor state using observed events.
  - Produce reconstructed events when notified of a missing observation.
  - Publish reconstructed events back into the `EventStream`.
- **Design Choice**:
  - Reconstruction logic is decoupled from scheduling.

#### Predictor (Abstract)
- **Purpose**: Encapsulate state estimation and uncertainty modeling.
- **Role**: Provide predictions and confidence estimates.
- **Responsibilities**:
  - `predict()` → advance state without observation.
  - `update(value)` → incorporate new observation.
  - `confidence()` → expose uncertainty for downstream reasoning.
- **Examples**:
  - Kalman Filters
  - Particle Filters
- **Design Choice**:
  - Predictor is agnostic to event timing and routing.

---

## Processor Layer
### `app/core/processor/`

#### EventProcessor
- **Purpose**: Manage lifecycle and integration of the Java CEP engine.
- **Role**: Bridge between Python-based event orchestration and Java-based CEP.
- **Responsibilities**:
  - Launch and terminate the CEP process.
  - Ensure event stream connectivity via ZeroMQ.
  - Coordinate execution and shutdown.
- **Design Choice**:
  - Allows CEP to evolve independently of the orchestration layer.

---

## CEP Layer (Java)
### `app/java/src/main/java/cep/`

#### CEPEngine (Abstract)
- **Purpose**: Abstract interface to a Complex Event Processing backend.
- **Role**: Detect atomic and complex patterns over event streams.
- **Responsibilities**:
  - Manage engine lifecycle.
  - Load and register pattern definitions.
  - Evaluate atomic and hierarchical event patterns.
- **Design Choice**:
  - CEP engine consumes the *entire* event stream
  - Allows confidence-aware reasoning at query time.

---

## Schema Layer
### `app/core/schema/`

#### Event
- **Purpose**: Representation of all events in the system.
- **Responsibilities**:
  - Encode observations, reconstructions, and metadata uniformly.
  - Preserve provenance, timing, and uncertainty.
- **Key Fields**:
  - `id`: unique event identifier
  - `src`: source identifier
  - `event_ts`: logical event time
  - `value`: observed or reconstructed value
  - `status`: `observed` or `reconstructed`
  - `confidence`: certainty estimate
  - `extras`: extensible metadata
- **Design Choice**:
  - Language-neutral schema shared across Python and Java.

---

## Pattern Schema (Java)
### `app/java/src/main/java/schema/pattern/`

#### Pattern
- **Purpose**: Represent atomic or complex event detections.
- **Responsibilities**:
  - Capture hierarchical pattern structure.
  - Maintain traceability to contributing events.
  - Propagate confidence through pattern compositions.
- **Design Choice**:
  - Maintain hierarchical structure, allowing multi-level compositions (complex patterns made of atomic or other complex subpatterns).  

---

## Utilities
### `app/core/utils/`

#### Logger (Abstract)
- **Purpose**: logs events for analysis and evaluation.
- **Role**: Passive observer of the event stream.
- **Responsibilities**:
  - Records all events in the event stream.
- **Design Choice**:
  - Ensures experimental reproducibility.
