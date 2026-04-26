# Reliable Complex Event Processing in Systems of Twinned Systems

This repository implements a reliability-aware complex event processing pipeline for systems of twinned systems

## Approach
Each constituent is governed by a **lifecycle statechart** with two orthogonal dimensions:

- **Belonging** – whether the system participates in the SoTS  
- **Health** – the operational condition of the system  

These statecharts control:
- when a system can contribute data  
- when it must be restricted

Reliability is enforced by constraining which combinations of belonging and health are allowed.

Reliability levels implemented:
- **Level 4 (Adaptive)** – Restricted roles with compensation for missing data  

---

## Architecture
The system is implemented as a **hybrid Python–Java architecture** (See [Architecture Overview](./docs/Architecture%20Overview.md) for a detailed breakdown):

- **Python layer**
  - Executes lifecycle statecharts (Itemis CREATE / Yakindu)
  - Controls event production based on belonging state
  - Performs compensation for missing or unreliable data  

- **Event stream**
  - ZeroMQ-based messaging layer connecting components  

- **Java layer**
  - Processes events using the Esper CEP engine  

Only **validated or compensated events** are forwarded to the CEP engine, ensuring that downstream processing operates on reliable inputs.
