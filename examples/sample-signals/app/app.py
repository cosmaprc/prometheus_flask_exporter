import time
import random

from flask import Flask, request
from prometheus_client import (
    CollectorRegistry,
    Histogram,
    process_collector,
    Counter,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

"""
Manual instrumentation example using https://prometheus.github.io/client_python/ directly and reproducing the metrics used
in this prometheus_flask_exporter example https://github.com/rycus86/prometheus_flask_exporter/tree/master/examples/sample-signals
which in the example are automatically exported by the prometheus_flask_exporter library
Simply follow the instructions in the README.md or at https://github.com/rycus86/prometheus_flask_exporter/tree/master/examples/sample-signals
to run the example and view the dashboard in Grafana
"""

# Custom metric collector registry
registry = CollectorRegistry()

# Add process_resident_memory_bytes and process_cpu_seconds_total metrics to the registry
process_collector.ProcessCollector(registry=registry)

# Add flask_http_request_duration_seconds_bucket and flask_http_request_duration_seconds_count metrics to the registry
flask_http_request_latency_histogram = Histogram(
    "flask_http_request_duration_seconds",
    "Represents the duration of request execution in different time intervals",
    ["status", "path"],
    registry=registry,
)

# Add flask_http_request_total metric to the registry
flask_http_request_total = Counter(
    "flask_http_request_total",
    "Tracks the total count of requests",
    [
        "status",
    ],
    registry=registry,
)

app = Flask(__name__)

endpoints = ("one", "two", "three", "four", "five", "error")


@app.before_request
def before_request():
    """Capture request start time before processing the request"""
    request.start_time = time.time()


@app.after_request
def after_request(response):
    """Calculate request duration and update metrics before returning the response"""
    duration = time.time() - request.start_time

    flask_http_request_total.labels(
        status=str(response.status_code),
    ).inc()

    flask_http_request_latency_histogram.labels(
        status=str(response.status_code),
        path=request.path,
    ).observe(duration)

    return response


@app.route("/metrics")
def metrics():
    return (
        generate_latest(registry),
        200,
        {"Content-Type": CONTENT_TYPE_LATEST},
    )


@app.route("/one")
def first_route():
    time.sleep(random.random() * 0.2)
    return "ok"


@app.route("/two")
def the_second():
    time.sleep(random.random() * 0.4)
    return "ok"


@app.route("/three")
def test_3rd():
    time.sleep(random.random() * 0.6)
    return "ok"


@app.route("/four")
def fourth_one():
    time.sleep(random.random() * 0.8)
    return "ok"


@app.route("/error")
def oops():
    return ":(", 500


if __name__ == "__main__":
    app.run("0.0.0.0", 5000, threaded=True)
