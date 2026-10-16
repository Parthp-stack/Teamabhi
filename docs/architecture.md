# High-Level Architecture & System Design

## 1. System Topology

```
                       STUDENT / TRAINER
                               |
                               v
                     React 18 / Vite Client
           (Monaco Editor, React Flow, Recharts)
                               |
                               | REST API (JWT Authenticated)
                               v
                     FastAPI Application Server
                               |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
   PostgreSQL / SQLite    OpenRouter API          Multi-Mode Sandbox
   (SQLAlchemy 2.0)       (Nemotron 3 Ultra)     (Docker / Isolated Proc)
        |                      |                      |
        v                      v                      v
  Knowledge Tracing       AI Questions &          Isolated Hidden Tests
  Bayesian Engine         Viva Evaluation         Process Termination
        |
        v
  Adaptive Engine
  (Weakest Prerequisite)
        |
        v
  Next Learning Activity
```

## 2. Integrity Analysis & Timeline Reconstruction Pipeline

```
Frontend Keystroke / Paste / Focus / Blur / Tab-Switch Buffer
                               |
                               | Periodic Batch POST (Every 4s)
                               v
                  `session_events` Database Table
                               |
                               v
                Integrity Engine Analysis Pipeline
                               |
            +------------------+------------------+
            |                  |                  |
            v                  v                  v
       LARGE_PASTE          NO_CYCLE         TAB_SWITCH
      (>120 chars)      (0 or 1 run)        (Blur events)
            |                  |                  |
            +------------------+------------------+
                               |
                               v
                `integrity_signals` Table
             (Strictly "Evidence for Human Review")
                               |
                               v
          Trainer Session Replay (3-Column Interface)
      [Timeline] <---> [Code Playback] <---> [Signal Jumps]
```

## 3. Bayesian Knowledge Tracing Model

The platform represents student proficiency on each concept as a bounded mastery metric $M \in [0, 100]$.

1. **Difficulty-Weighted Adaptation**:
   - $\text{EASY}$: Boost factor $5.0$, Penalty factor $7.0$
   - $\text{MEDIUM}$: Boost factor $8.0$, Penalty factor $6.0$
   - $\text{HARD}$: Boost factor $12.0$, Penalty factor $4.0$

2. **Diminishing Returns & Floor Damping**:
   $$\Delta_{\text{correct}} = W_{\text{correct}} \times \left(0.4 + 0.6 \times \frac{100 - M_{\text{current}}}{100}\right)$$
   $$\Delta_{\text{wrong}} = - W_{\text{wrong}} \times \left(0.4 + 0.6 \times \frac{M_{\text{current}}}{100}\right)$$

3. **Status Thresholds**:
   - $\ge 80\%$: `MASTERED`
   - $50\% - 79\%$: `LEARNING`
   - $< 50\%$: `WEAK`
   - Prerequisite $< 65\%$: `LOCKED`

## 4. Adaptive Learning Rationale Engine

The adaptive algorithm follows this decision sequence:
1. Load student's mastery vector across all course concepts.
2. Evaluate prerequisite competency constraints along the concept DAG.
3. Identify eligible unmastered concepts ($< 85\%$).
4. Pick the weakest eligible concept (ensuring prerequisite mastery before dependent topics).
5. Match question difficulty to current mastery:
   - $< 40\% \rightarrow \text{EASY}$
   - $40\% - 74\% \rightarrow \text{MEDIUM}$
   - $\ge 75\% \rightarrow \text{HARD}$
6. Deliver question with human-interpretable rationale.
