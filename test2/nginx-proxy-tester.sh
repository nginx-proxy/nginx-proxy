#!/bin/bash
###############################################################################
#                                                                             #
# This script is meant to run the test suite from a Docker container.         #
#                                                                             #
# This is usefull when you want to run the test suite from Mac or             #
# Docker Toolbox.                                                             #
#                                                                             #
###############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARGS="$@"

# check requirements
if [[ "$(docker images -q nginx-proxy-tester 2>/dev/null)" == "" ]]; then
	echo "> Building nginx-proxy-tester image..."
	docker build -t nginx-proxy-tester -f $DIR/requirements/Dockerfile-nginx-proxy-tester $DIR/requirements
fi

# delete python cache
[[ -d "${DIR}/__pycache__" ]] && rm "${DIR}/__pycache__" -rf

# run the nginx-proxy-tester container setting the correct value for the working dir in order for 
# docker-compose to work properly when run from within that container.
docker run --rm -it \
	-v ${DIR}:/${DIR} \
	-v ${DIR}/__pycache__/ \
	-w ${DIR} \
	-v /var/run/docker.sock:/var/run/docker.sock \
	nginx-proxy-tester "${ARGS}"
PYTEST_EXIT_CODE=$?

# delete python cache
[[ -d "${DIR}/__pycache__" ]] && rm "${DIR}/__pycache__" -rf

exit ${PYTEST_EXIT_CODE}
