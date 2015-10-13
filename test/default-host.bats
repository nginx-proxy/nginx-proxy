#!/usr/bin/env bats
load test_helpers

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	CIDS=( $(docker ps -q --filter "label=bats-type=web") )
	if [ ${#CIDS[@]} -gt 0 ]; then
		docker stop ${CIDS[@]} >&2
	fi
}


@test "[$TEST_FILE] DEFAULT_HOST=web1.bats" {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-1

	# GIVEN a webserver with VIRTUAL_HOST set to web.bats
	prepare_web_container bats-web 80 -e VIRTUAL_HOST=web.bats

	# WHEN nginx-proxy runs with DEFAULT_HOST set to web.bats
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro -e DEFAULT_HOST=web.bats
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"

	# THEN querying the proxy without Host header → 200
	run curl_container $SUT_CONTAINER / --head
	assert_output -l 0 $'HTTP/1.1 200 OK\r'

	# THEN querying the proxy with any other Host header → 200
	run curl_container $SUT_CONTAINER / --head --header "Host: something.I.just.made.up"
	assert_output -l 0 $'HTTP/1.1 200 OK\r'
}
