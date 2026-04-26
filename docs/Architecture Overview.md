# Architecture Overview
This section describes the core architectural layers, the main classes within each layer, and their responsibilities.
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

#### ModelAdaptor
- **Purpose**: Interface between generated statecharts and the runtime system.
- **Role**: Encapsulates a constituent’s lifecycle statechart.
- **Responsibilities**:
  - Execute and manage the underlying statechart.
  - Maintain state snapshot:
    - Belonging (e.g., passive, active, participating)
    - Health (e.g., ideal → failed)
  - Provide transition (e.g., `join_sos`, `degrade`, `improve`).
  - Emit lifecycle signals and log transitions.
- **Design Choice**:
  - Hides statechart complexity

#### LifecycleManager
- **Purpose**: Coordinate lifecycle state across all constituents.
- **Role**: Central controller for system-level lifecycle behaviour.
- **Responsibilities**:
  - Register and manage `ConstituentContext` objects.
  - Control transitions (activation, health, belonging).
  - Provide system-wide state summaries.
  - Enable coordinated adaptation across constituents.
- **Design Choice**:
  - Centralizes lifecycle logic without coupling components.

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

## Compensation Layer
### `app/core/compensation/`

#### Reconstructor
- **Purpose**: Detect and reconstruct missing events in the event stream.
- **Role**: Creates replacement events using prediction.
- **Responsibilities**:
  - Monitor incoming events to detect missing observations.
  - Maintain predictor state using observed events.
  - Produce reconstructed events when required.
  - Emit reconstructed events back into the `EventStream`.
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

#### EventConsumer (Interface)
- **Purpose**: Common interface for all components that react to events.
- **Role**: Defines the contract for event-driven processing.
- **Responsibilities**:
  - Consume immutable `Event` objects via `consume_event(event)`.
- **Design Choice**:
  - Ensures uniform handling across reconstructors, loggers, coordinators, and CEP adapters.


#### EventGenerator (Interface)
- **Purpose**: Interface for components that produce events from data sources.
- **Role**: Defines how event-producing entities generate and emit events into the system.
- **Responsibilities**:
  - Generate event payloads (`generate_event()`).
  - Emit events onto the `EventStream` (`emit_event()`).
- **Design Choice**:
  - Ensures consistent event production across all sources.
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


## Statechart Layer
### `app/state_charts/`
#### Generated Statecharts (Yakindu)
- **Purpose**: Formal specification of lifecycle behaviour.
- **Role**: Define valid states, transitions, and constraints.
- **Responsibilities**:
  - Enforce valid transitions.
  - Emit observable signals.
  - Support timed/event-driven execution.
- **Design Choice**:
  - Automatically generated from models developed in ItemisCreate

---