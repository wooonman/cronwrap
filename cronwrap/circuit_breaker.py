"""Circuit breaker: pause a job after N consecutive failures."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CircuitBreakerConfig:
    enabled: bool = False
    failure_threshold: int = 3      # open after this many consecutive failures
    recovery_timeout: int = 300     # seconds before moving to half-open
    job_name: str = "default"
    state_dir: str = "/tmp/cronwrap/circuit"

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerConfig":
        return cls(
            enabled=data.get("enabled", False),
            failure_threshold=data.get("failure_threshold", 3),
            recovery_timeout=data.get("recovery_timeout", 300),
            job_name=data.get("job_name", "default"),
            state_dir=data.get("state_dir", "/tmp/cronwrap/circuit"),
        )


@dataclass
class CircuitState:
    status: str = "closed"          # closed | open | half-open
    consecutive_failures: int = 0
    opened_at: Optional[float] = None
    last_failure_at: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "consecutive_failures": self.consecutive_failures,
            "opened_at": self.opened_at,
            "last_failure_at": self.last_failure_at,
        }


def _state_path(cfg: CircuitBreakerConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.job_name}.json"


def _read_state(cfg: CircuitBreakerConfig) -> CircuitState:
    p = _state_path(cfg)
    if not p.exists():
        return CircuitState()
    try:
        data = json.loads(p.read_text())
        return CircuitState(**data)
    except Exception:
        return CircuitState()


def _write_state(cfg: CircuitBreakerConfig, state: CircuitState) -> None:
    p = _state_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.as_dict()))


def is_open(cfg: CircuitBreakerConfig) -> bool:
    """Return True if the circuit is open (job should be skipped)."""
    if not cfg.enabled:
        return False
    state = _read_state(cfg)
    if state.status == "open":
        elapsed = time.time() - (state.opened_at or 0)
        if elapsed >= cfg.recovery_timeout:
            state.status = "half-open"
            _write_state(cfg, state)
            return False
        return True
    return False


def record_outcome(cfg: CircuitBreakerConfig, success: bool) -> CircuitState:
    """Update circuit state based on run outcome."""
    if not cfg.enabled:
        return CircuitState()
    state = _read_state(cfg)
    now = time.time()
    if success:
        state = CircuitState(status="closed")
    else:
        state.consecutive_failures += 1
        state.last_failure_at = now
        if state.consecutive_failures >= cfg.failure_threshold:
            state.status = "open"
            state.opened_at = now
    _write_state(cfg, state)
    return state


def reset_circuit(cfg: CircuitBreakerConfig) -> None:
    """Manually reset the circuit to closed."""
    _write_state(cfg, CircuitState())
