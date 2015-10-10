#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	CIDS=( $(docker ps -q --filter "label=bats-type=web") )
	if [ ${#CIDS[@]} -gt 0 ]; then
		docker stop ${CIDS[@]} >&2
	fi
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	# GIVEN nginx-proxy
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
}


@test "[$TEST_FILE] nginx-proxy defaults to the service running on port 80" {
	# WHEN
	prepare_web_container bats-web-${TEST_FILE}-1 "80 90" -e VIRTUAL_HOST=web.bats

	# THEN
	assert_response_is_from_port 80
}


@test "[$TEST_FILE] VIRTUAL_PORT=90 while port 80 is also exposed" {
	# GIVEN
	prepare_web_container bats-web-${TEST_FILE}-2 "80 90" -e VIRTUAL_HOST=web.bats -e VIRTUAL_PORT=90

	# THEN
	assert_response_is_from_port 90
}


@test "[$TEST_FILE] single exposed port != 80" {
	# GIVEN
	prepare_web_container bats-web-${TEST_FILE}-3 1234 -e VIRTUAL_HOST=web.bats

	# THEN
	assert_response_is_from_port 1234
}


# assert querying nginx-proxy provides a response from the expected port of the web container
# $1 port we are expecting an response from
function assert_response_is_from_port {
	local -r port=$1
	run curl_container $SUT_CONTAINER /data --header "Host: web.bats"
	assert_output "answer from port $port"
}

