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
	# GIVEN
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
}


@test "[$TEST_FILE] VIRTUAL_HOST=*.wildcard.bats" {
	# WHEN
	prepare_web_container bats-wildcard-hosts-1 80 -e VIRTUAL_HOST=*.wildcard.bats

	# THEN
	assert_200 f00.wildcard.bats
	assert_200 bar.wildcard.bats
	assert_503 unexpected.host.bats
}

@test "[$TEST_FILE] VIRTUAL_HOST=wildcard.bats.*" {
	# WHEN
	prepare_web_container bats-wildcard-hosts-2 80 -e VIRTUAL_HOST=wildcard.bats.*

	# THEN
	assert_200 wildcard.bats.f00
	assert_200 wildcard.bats.bar
	assert_503 unexpected.host.bats
}

@test "[$TEST_FILE] VIRTUAL_HOST=~^foo\.bar\..*\.bats" {
	# WHEN
	prepare_web_container bats-wildcard-hosts-2 80 -e VIRTUAL_HOST=~^foo\.bar\..*\.bats

	# THEN
	assert_200 foo.bar.whatever.bats
	assert_200 foo.bar.why.not.bats
	assert_503 unexpected.host.bats

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
