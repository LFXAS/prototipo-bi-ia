#!/usr/bin/env bash
set -euo pipefail

"$@" &
sqlserver_pid=$!

/usr/local/bin/bootstrap-adventureworks.sh &
bootstrap_pid=$!

shutdown() {
    kill -TERM "${sqlserver_pid}" 2>/dev/null || true
    wait "${sqlserver_pid}" 2>/dev/null || true
}

trap shutdown TERM INT

set +e
wait "${sqlserver_pid}"
status=$?
kill "${bootstrap_pid}" 2>/dev/null || true
wait "${bootstrap_pid}" 2>/dev/null || true
exit "${status}"
