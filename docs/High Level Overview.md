# Structural Overview  
This section gives a high level overview tool

## High-Level Flow  

1. **Streams** generate raw data (may include missing values).  
2. **Coordinator** routes events into the `observed` partition.  
   - Handles scheduling, and if data is missing at a tick, detects gaps.  
3. **Reconstructors** process every event:  
   - If observed → append reliability metadata and forward to `reconstructed`.  
   - If missing → impute via predictor, add `confidence`, and forward to `reconstructed`.   
4. **CEP Engine** subscribes only to reconstructed events, ensuring it sees a complete stream.  
   - Emits pattern matches.  

---

## Communication Structure  

### Partition Responsibilities  

- **Observed**: Holds raw sensor events directly from streams.  
- **Reconstructed**: Holds all events (observed passthrough + imputed), with appended reliability metadata.  

Partitions help with modularity
- Consumers (CEP, loggers, UIs, reconstructors) only subscribe to partitions relevant to their role.  
- New partitions (e.g., `late`, `anomaly`) can be added without disrupting the pipeline.  

---

## Design Principles  
- **Partitioned by lifecycle**: Events are grouped by their processing stage, not by source, so each consumer gets exactly the data it needs.  
- **Separation of concerns**: Stream generation, reconstruction, and pattern detection are decoupled, enabling independent testing and modular upgrades.  
- **Extensibility**: Additional partitions or new messaging backends (e.g., Kafka, MQTT) can be introduced with minimal changes.  
---