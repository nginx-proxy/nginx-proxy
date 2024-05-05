#!/bin/bash
set -u

trap '[ ${#PIDS[@]} -gt 0 ] && kill -TERM ${PIDS[@]}' TERM
declare -a PIDS

for port in $WEB_PORTS; do
	echo starting a web server listening on port "$port";
	/webserver.py "$port" &
	PIDS+=($!)
done

wait "${PIDS[@]}"
trap - TERM
wait "${PIDS[@]}"
