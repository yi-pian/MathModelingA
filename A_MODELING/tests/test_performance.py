from core.performance import benchmark, timed


def test_timing_helpers():
    @timed
    def add(a, b): return a + b
    assert add(2, 3) == 5 and add.last_seconds is not None
    result = benchmark(add, 2, 3, repeats=2, warmup=0)
    assert result["runs"] == 2 and result["min_seconds"] >= 0
