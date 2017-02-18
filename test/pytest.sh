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
echo "> Building nginx-proxy-tester image..."
docker build -t nginx-proxy-tester -f $DIR/requirements/Dockerfile-nginx-proxy-tester $DIR/requirements

# run the nginx-proxy-tester container setting the correct value for the working dir in order for 
# docker-compose to work properly when run from within that container.
exec docker run --rm -it \
	-v ${DIR}:/${DIR} \
	-w ${DIR} \
	-v /var/run/docker.sock:/var/run/docker.sock \
	nginx-proxy-tester ${ARGS}
