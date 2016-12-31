#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	stop_bats_containers web
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	# GIVEN nginx-proxy
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"
}


@test "[$TEST_FILE] nginx-proxy defaults to the service running on port 80" {
	# WHEN
	prepare_web_container bats-web-${TEST_FILE}-1 "80 90" -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-web-${TEST_FILE}-1
	sleep 1

	# THEN
	assert_response_is_from_port 80
}


@test "[$TEST_FILE] VIRTUAL_PORT=90 while port 80 is also exposed" {
	# GIVEN
	prepare_web_container bats-web-${TEST_FILE}-2 "80 90" -e VIRTUAL_HOST=web.bats -e VIRTUAL_PORT=90
	dockergen_wait_for_event $SUT_CONTAINER start bats-web-${TEST_FILE}-2
	sleep 1

	# THEN
	assert_response_is_from_port 90
}


@test "[$TEST_FILE] single exposed port != 80" {
	# GIVEN
	prepare_web_container bats-web-${TEST_FILE}-3 1234 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-web-${TEST_FILE}-3
	sleep 1

	# THEN
	assert_response_is_from_port 1234
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}


# assert querying nginx-proxy provides a response from the expected port of the web container
# $1 port we are expecting an response from
function assert_response_is_from_port {
	local -r port=$1
	run curl_container $SUT_CONTAINER /port --header "Host: web.bats"
	assert_output "answer from port $port"
}

