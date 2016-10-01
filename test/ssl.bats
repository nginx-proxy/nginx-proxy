#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	stop_bats_containers web
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro -v ${DIR}/lib/ssl:/etc/nginx/certs:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"
}

@test "[$TEST_FILE] test SSL for VIRTUAL_HOST=*.nginx-proxy.bats" {
	# WHEN
	prepare_web_container bats-ssl-hosts-1 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-1
	sleep 1

	# THEN
	assert_301 test.nginx-proxy.bats
	assert_200_https test.nginx-proxy.bats
}

@test "[$TEST_FILE] test HTTPS_METHOD=nohttp" {
	# WHEN
	prepare_web_container bats-ssl-hosts-2 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats \
		-e HTTPS_METHOD=nohttp
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-2
	sleep 1

	# THEN
	assert_503 test.nginx-proxy.bats
	assert_200_https test.nginx-proxy.bats
}

@test "[$TEST_FILE] test HTTPS_METHOD=noredirect" {
	# WHEN
	prepare_web_container bats-ssl-hosts-3 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats \
		-e HTTPS_METHOD=noredirect
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-3
	sleep 1

	# THEN
	assert_200 test.nginx-proxy.bats
	assert_200_https test.nginx-proxy.bats
}

@test "[$TEST_FILE] test SSL Strict-Transport-Security" {
	# WHEN
	prepare_web_container bats-ssl-hosts-4 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-1
	sleep 1

	# THEN
	assert_301 test.nginx-proxy.bats
	assert_200_https test.nginx-proxy.bats
    assert_output -p "Strict-Transport-Security: max-age=31536000"
}

@test "[$TEST_FILE] test HTTPS_METHOD=noredirect disables Strict-Transport-Security" {
	# WHEN
	prepare_web_container bats-ssl-hosts-5 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats \
		-e HTTPS_METHOD=noredirect
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-3
	sleep 1

	# THEN
	assert_200 test.nginx-proxy.bats
	assert_200_https test.nginx-proxy.bats
    refute_output -p "Strict-Transport-Security: max-age=31536000"
}

@test "[$TEST_FILE] test HTTPS_METHOD=nohttps" {
	# WHEN
	prepare_web_container bats-ssl-hosts-6 "80" \
		-e VIRTUAL_HOST=*.nginx-proxy.bats \
		-e CERT_NAME=nginx-proxy.bats \
		-e HTTPS_METHOD=nohttps
	dockergen_wait_for_event $SUT_CONTAINER start bats-ssl-hosts-6
	sleep 1

	# THEN
	assert_down_https test.nginx-proxy.bats
	assert_200 test.nginx-proxy.bats
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

# assert that querying nginx-proxy with the given Host header produces a `HTTP 503` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_301 {
	local -r host=$1

	run curl_container $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 301 Moved Permanently\r'
}

# assert that querying nginx-proxy with the given Host header fails because the host is down
# $1 Host HTTP header to use when querying nginx-proxy
function assert_down_https {
	local -r host=$1

	run curl_container_https $SUT_CONTAINER / --head --header "Host: $host"
	assert_failure
}

# assert that querying nginx-proxy with the given Host header produces a `HTTP 200` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_200_https {
	local -r host=$1

	run curl_container_https $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 200 OK\r'
}

# assert that querying nginx-proxy with the given Host header produces a `HTTP 503` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_503_https {
	local -r host=$1

	run curl_container_https $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'
}

# assert that querying nginx-proxy with the given Host header produces a `HTTP 503` response
# $1 Host HTTP header to use when querying nginx-proxy
function assert_301_https {
	local -r host=$1

	run curl_container_https $SUT_CONTAINER / --head --header "Host: $host"
	assert_output -l 0 $'HTTP/1.1 301 Moved Permanently\r'
}
