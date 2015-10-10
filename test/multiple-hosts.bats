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
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
}

@test "[$TEST_FILE] nginx-proxy forwards requests for 2 hosts" {
	# WHEN a container runs a web server with VIRTUAL_HOST set for multiple hosts
	prepare_web_container bats-multiple-hosts-1 80 -e VIRTUAL_HOST=multiple-hosts-1-A.bats,multiple-hosts-1-B.bats

	# THEN querying the proxy without Host header → 503
	run curl_container $SUT_CONTAINER / --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'

	# THEN querying the proxy with unknown Host header → 503
	run curl_container $SUT_CONTAINER /data --header "Host: webFOO.bats" --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'

	# THEN
	run curl_container $SUT_CONTAINER /data --header 'Host: multiple-hosts-1-A.bats'
	assert_output "answer from port 80"

	# THEN
	run curl_container $SUT_CONTAINER /data --header 'Host: multiple-hosts-1-B.bats'
	assert_output "answer from port 80"
}
