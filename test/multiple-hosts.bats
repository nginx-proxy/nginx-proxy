#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	docker ps -q --filter "label=bats-type=web" | xargs -r docker stop >&2
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
}

@test "[$TEST_FILE] nginx-proxy forwards requests for 2 hosts" {
	# WHEN a container runs a web server with VIRTUAL_HOST set for multiple hosts
	docker_clean bats-multiple-hosts-1
	run docker run -d \
		--label bats-type="web" \
		--name bats-multiple-hosts-1 \
		-e VIRTUAL_HOST=multiple-hosts-1-A.bats,multiple-hosts-1-B.bats \
		--expose 80 \
		-w /data \
		python:3 python -m http.server 80
	assert_success
	run retry 5 1s curl_container bats-multiple-hosts-1 / --head
	assert_output -l 0 $'HTTP/1.0 200 OK\r'

	# THEN querying the proxy without Host header → 503
	run curl_container $SUT_CONTAINER / --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'

	# THEN querying the proxy with unknown Host header → 503
	run curl_container $SUT_CONTAINER /data --header "Host: webFOO.bats" --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'

	# THEN
	run curl_container $SUT_CONTAINER / --head --header 'Host: multiple-hosts-1-A.bats'
	assert_output -l 0 $'HTTP/1.1 200 OK\r' || (echo $output; echo $status; false)

	# THEN
	run curl_container $SUT_CONTAINER / --head --header 'Host: multiple-hosts-1-B.bats'
	assert_output -l 0 $'HTTP/1.1 200 OK\r'
}
