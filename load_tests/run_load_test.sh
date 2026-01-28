#!/bin/bash
# Run load tests against the FCRA platform
#
# Usage:
#   ./load_tests/run_load_test.sh                    # Interactive UI at http://localhost:8089
#   ./load_tests/run_load_test.sh headless            # Headless: 50 users, 5/sec ramp, 5 min
#   ./load_tests/run_load_test.sh headless 100 10 10m # Custom: 100 users, 10/sec, 10 min
#
# Prerequisites:
#   pip install locust

set -e

HOST="${LOAD_TEST_HOST:-http://localhost:5001}"
LOCUSTFILE="load_tests/locustfile.py"

if [ ! -f "$LOCUSTFILE" ]; then
    echo "Error: $LOCUSTFILE not found. Run from project root."
    exit 1
fi

if ! command -v locust &> /dev/null; then
    echo "Installing locust..."
    pip install locust
fi

if [ "$1" = "headless" ]; then
    USERS="${2:-50}"
    SPAWN_RATE="${3:-5}"
    RUN_TIME="${4:-5m}"

    echo "=== FCRA Load Test (Headless) ==="
    echo "Host: $HOST"
    echo "Users: $USERS, Spawn rate: $SPAWN_RATE/s, Duration: $RUN_TIME"
    echo ""

    locust -f "$LOCUSTFILE" \
        --host "$HOST" \
        --headless \
        -u "$USERS" \
        -r "$SPAWN_RATE" \
        --run-time "$RUN_TIME" \
        --csv=load_tests/results \
        --html=load_tests/report.html

    echo ""
    echo "Results saved to:"
    echo "  load_tests/results_stats.csv"
    echo "  load_tests/report.html"
else
    echo "=== FCRA Load Test (Interactive) ==="
    echo "Host: $HOST"
    echo "Open http://localhost:8089 in your browser"
    echo ""

    locust -f "$LOCUSTFILE" --host "$HOST"
fi
