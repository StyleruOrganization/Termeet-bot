from prometheus_client import (
    Histogram,
)

get_feedback_latency = Histogram(
    "get_feedback_latency",
    "Get feedback latency in seconds",
    ["method"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)
