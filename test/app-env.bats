#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	stop_bats_containers web
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	# GIVEN
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro -e APP_KEY=green
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"
}


@test "[$TEST_FILE] VIRTUAL_HOST=green.app.bats APP_KEY=green" {
	# WHEN
	prepare_web_container bats-app-env-1 80 -e VIRTUAL_HOST=green.app.bats -e APP_KEY=green
	dockergen_wait_for_event $SUT_CONTAINER start bats-app-env-1
	sleep 1

	# THEN
	assert_200 green.app.bats
	  assert_output -p "X-App-Key: green"
}

@test "[$TEST_FILE] VIRTUAL_HOST=blue.app.bats APP_KEY=blue" {
	# WHEN
	prepare_web_container bats-app-env-2 80 -e VIRTUAL_HOST=blue.app.bats -e APP_KEY=blue
	dockergen_wait_for_event $SUT_CONTAINER start bats-app-env-2
	sleep 1

	# THEN
	assert_503 blue.app.bats
	  refute_output -p "X-App-Key: blue"
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}


# assert that querying nginx-proxy with the given Host header produces a `HTTP 200` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_200 {
	local -r host=$1

	run curl_container $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 200 OK\r'
}

# assert that querying nginx-proxy with the given Host header produces a `HTTP 503` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_503 {
	local -r host=$1

	run curl_container $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'
}
