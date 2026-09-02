"""Small, opt-in timing and benchmarking helpers."""

from __future__ import annotations

from functools import wraps
from statistics import mean, median
from time import perf_counter


def timed(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = function(*args, **kwargs)
        wrapper.last_seconds = perf_counter() - start
        return result
    wrapper.last_seconds = None
    return wrapper


def benchmark(function, *args, repeats=5, warmup=1, **kwargs):
    if repeats < 1 or warmup < 0:
        raise ValueError("repeats must be positive and warmup nonnegative")
    for _ in range(warmup):
        function(*args, **kwargs)
    times = []
    for _ in range(repeats):
        start = perf_counter()
        function(*args, **kwargs)
        times.append(perf_counter() - start)
    return {"runs": repeats, "min_seconds": min(times), "mean_seconds": mean(times), "median_seconds": median(times), "all_seconds": times}
