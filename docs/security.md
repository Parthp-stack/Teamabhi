# Security Architecture & Sandbox Controls

## 1. Untrusted Code Isolation Model

Student-submitted source code is treated as inherently hostile.

### Docker Sandbox Isolation
- **Network Isolation**: Containers are started with `--network none`, eliminating external socket access, reverse shells, or HTTP requests.
- **Resource Constraints**:
  - Memory: `--memory 128m` (prevents OOM exhaustion attacks).
  - CPU: `--nano-cpus 500000000` (limits execution to 0.5 cores, preventing CPU starvation).
  - PIDs: `--pids-limit 50` (prevents fork bombs).
- **Execution Timeouts**: Execution terminates after 2-5 seconds.
- **Privilege Separation**: Containers run under unprivileged non-root user `sandboxuser` (`UID 10001`).
- **Filesystem Isolation**: Code is placed in a temporary directory mounted read-only (`:ro`).
- **Automated Destruction**: Container is removed with force in a `finally` block.

### Static AST & Fallback Process Sandbox
When running in environments where Docker daemon is not active:
- **Static AST Analysis**: The code AST is parsed before execution. Any import of banned modules (`os`, `sys`, `subprocess`, `socket`, `shutil`, `ctypes`, etc.) or execution of builtins (`eval`, `exec`, `__import__`, `open`) raises `SandboxSecurityException` and returns `SECURITY_BLOCKED`.
- **Isolated Process Execution**: Executed with `-I` (isolated mode) in an ephemeral directory destroyed immediately after execution.

## 2. Evidence-Based Integrity (No Automatic Cheating Verdicts)

A core ethical requirement of the platform is that **no automated cheating verdict is ever made**.
- Signals are recorded as **"Integrity Evidence for Human Review"**.
- Each signal references the exact `event_id` and timestamp.
- Signals:
  - `LARGE_PASTE`: Code insertions $\ge 120$ characters.
  - `FAST_CODE`: Extreme code insertion rate within $< 2$ seconds.
  - `NO_CYCLE`: Submissions lacking an iterative write $\rightarrow$ run $\rightarrow$ fix workflow.
  - `TAB_SWITCH`: Window blur or document visibility changes.
  - `UNIFORM_TYPING`: Abnormally low standard deviation in keystroke intervals.

## 3. Secret Management & Credential Protection
- `OPENROUTER_API_KEY`, `JWT_SECRET`, and `DATABASE_URL` are strictly loaded on the backend from `.env`.
- Frontend JavaScript bundle has **zero** access to provider API keys.
- AI requests are mediated exclusively through backend controller abstractions (`/api/ai/...`).
- Hidden test cases are filtered out on the backend and never included in `CodingProblemResponse`.
- Password hashes use salt rounds of 12 via `bcrypt`. Plaintext passwords are never stored or logged.
