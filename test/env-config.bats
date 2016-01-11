#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}
HOST=web.bats
MOUNT="-v /var/run/docker.sock:/tmp/docker.sock:ro"

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected container running with VIRTUAL_HOST or VIRUTAL_PORT set
	CIDS=( $(docker ps -q --filter "label=bats-type=web") )
	if [ ${#CIDS[@]} -gt 0 ]; then
		docker stop ${CIDS[@]} >&2
	fi
}


@test "[$TEST_FILE] run nginx-proxy without USE_IP_HASH" {
	# WHEN multiple containers runs without USE_IP_HASH
	run nginxproxy $SUT_CONTAINER $MOUNT
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
	prepare_web_container bats-web-${TEST_FILE}-1 80 -e VIRTUAL_HOST=$HOST
	prepare_web_container bats-web-${TEST_FILE}-2 90 -e VIRTUAL_HOST=$HOST

	# THEN querying nginx-proxy twice should return different responses
	query_nginx; local response1="$output"
	query_nginx; local response2="$output"
	refute_equal "$response1" "$response2"
}

@test "[$TEST_FILE] run nginx-proxy with USE_IP_HASH=1" {
	# WHEN multiple containers runs with USE_IP_HASH=1
	run nginxproxy $SUT_CONTAINER $MOUNT
	assert_success
	docker_wait_for_log $SUT_CONTAINER 3 "Watching docker events"
	prepare_web_container bats-web-${TEST_FILE}-1 80 -e VIRTUAL_HOST=$HOST -e USE_IP_HASH=1
	prepare_web_container bats-web-${TEST_FILE}-2 90 -e VIRTUAL_HOST=$HOST -e USE_IP_HASH=1

	# THEN querying nginx-proxy twice should return the same response
	query_nginx; local response1="$output"
	query_nginx; local response2="$output"
	assert_equal "$response1" "$response2"
}

# helper functions from jasonkarns/bats-assert

function flunk {
	{ 	if [ "$#" -eq 0 ]; then cat -
		else echo "$@"
		fi
	} | sed "s:${BATS_TMPDIR}:\${BATS_TMPDIR}:g" >&2
	return 1
}

function query_nginx {
	run curl_container $SUT_CONTAINER /data --header "Host: $HOST"
}

function assert_equal {
	if [ "$1" != "$2" ]; then
	{	echo "expected: $1"
		echo "actual  : $2"
	} | flunk
	fi
}

function refute_equal {
	if [ "$1" = "$2" ]; then
		flunk "unexpectedly equal: $1"
	fi
}
