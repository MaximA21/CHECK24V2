import time
import functools
from typing import Dict, Optional
from contextvars import ContextVar
from dataclasses import dataclass, field
import asyncio


@dataclass
class ProfilingData:
    start_time: float
    measurements: Dict[str, float] = field(default_factory=dict)
    nested_level: int = 0


# Context für request-spezifisches Profiling
_profiling_context: ContextVar[Optional[ProfilingData]] = ContextVar('profiling_context', default=None)


def start_profiling():
    """Startet eine neue Profiling-Session"""
    _profiling_context.set(ProfilingData(start_time=time.time()))


def get_profiling_data() -> Optional[ProfilingData]:
    """Holt aktuelle Profiling-Daten"""
    return _profiling_context.get()


class ProfilingBlock:
    """Context Manager für Zeitmessung eines Code-Blocks"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        profiling_data = get_profiling_data()
        if profiling_data:
            profiling_data.nested_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        profiling_data = get_profiling_data()
        if profiling_data:
            profiling_data.measurements[self.name] = duration
            profiling_data.nested_level -= 1


def profile_block(name: str):
    """Decorator für Funktions-Profiling"""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with ProfilingBlock(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with ProfilingBlock(name):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator