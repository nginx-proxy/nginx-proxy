#!/bin/bash
###############################################################################
#                                                                             #
# This script is meant to run the test suite from a Docker container.         #
#                                                                             #
# This is usefull when you want to run the test suite from Mac or             #
# Docker Toolbox.                                                             #
#                                                                             #
###############################################################################

# Returns the absolute directory path to this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARGS=("$@")

# check requirements
echo "> Building nginx-proxy-tester image..."
docker build -t nginx-proxy-tester -f "${DIR}/requirements/Dockerfile-nginx-proxy-tester" "${DIR}/requirements"

# run the nginx-proxy-tester container setting the correct value for the working dir in order for 
# docker-compose to work properly when run from within that container.
exec docker run --rm -it --name "nginx-proxy-pytest" \
  --volume "/var/run/docker.sock:/var/run/docker.sock" \
  --volume "${DIR}:${DIR}" \
  --workdir "${DIR}" \
  nginx-proxy-tester "${ARGS[@]}"