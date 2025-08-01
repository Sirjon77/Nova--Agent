from nova import metrics
def test_metrics_labels():
    metrics.tasks_executed.inc()
    metrics.memory_items.set(42)
    assert metrics.memory_items._value.get() == 42
