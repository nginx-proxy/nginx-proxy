#!/bin/sh
###############################################################################
#                                                                             #
# This script is meant to run the test suite from a Docker container.         #
#                                                                             #
# This is usefull when you want to run the test suite from Mac or             #
# Docker Toolbox.                                                             #
#                                                                             #
###############################################################################

# Returns the absolute directory path to this script
TESTDIR=$(cd "${0%/*}" && pwd) || exit 1
DIR=$(cd "${TESTDIR}/.." && pwd) || exit 1

# check requirements
echo "> Building nginx-proxy-tester image..."
docker build --pull -t nginx-proxy-tester \
  -f "${TESTDIR}/requirements/Dockerfile-nginx-proxy-tester" \
  "${TESTDIR}/requirements" \
  || exit 1

# run the nginx-proxy-tester container setting the correct value for the working dir 
# in order for docker compose to work properly when run from within that container.
exec docker run --rm -it --name "nginx-proxy-pytest" \
  --volume "/var/run/docker.sock:/var/run/docker.sock" \
  --volume "${DIR}:${DIR}" \
  --workdir "${TESTDIR}" \
  nginx-proxy-tester "$@"
