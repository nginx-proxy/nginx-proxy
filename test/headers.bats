#!/usr/bin/env bats
load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected container running with VIRTUAL_HOST or VIRUTAL_PORT set
	stop_bats_containers web
}


@test "[$TEST_FILE] start a nginx-proxy container" {
	# GIVEN
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"
}

@test "[$TEST_FILE] nginx-proxy passes arbitrary header" {
	# WHEN
	prepare_web_container bats-host-1 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-1
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Foo: Bar" -H "Host: web.bats"
	assert_output -l 'Foo: Bar'
}

##### Testing the handling of X-Forwarded-For #####

@test "[$TEST_FILE] nginx-proxy generates X-Forwarded-For" {
	# WHEN
	prepare_web_container bats-host-2 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-2
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Host: web.bats"
	assert_output -p 'X-Forwarded-For:'
}

@test "[$TEST_FILE] nginx-proxy passes X-Forwarded-For" {
	# WHEN
	prepare_web_container bats-host-3 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-3
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "X-Forwarded-For: 1.2.3.4" -H "Host: web.bats"
	assert_output -p 'X-Forwarded-For: 1.2.3.4, '
}

##### Testing the handling of X-Forwarded-Proto #####

@test "[$TEST_FILE] nginx-proxy generates X-Forwarded-Proto" {
	# WHEN
	prepare_web_container bats-host-4 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-4
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Host: web.bats"
	assert_output -l 'X-Forwarded-Proto: http'
}

@test "[$TEST_FILE] nginx-proxy passes X-Forwarded-Proto" {
	# WHEN
	prepare_web_container bats-host-5 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-5
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "X-Forwarded-Proto: https" -H "Host: web.bats"
	assert_output -l 'X-Forwarded-Proto: https'
}

##### Testing the handling of X-Forwarded-Port #####

@test "[$TEST_FILE] nginx-proxy generates X-Forwarded-Port" {
	# WHEN
	prepare_web_container bats-host-6 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-6
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Host: web.bats"
	assert_output -l 'X-Forwarded-Port: 80'
}

@test "[$TEST_FILE] nginx-proxy passes X-Forwarded-Port" {
	# WHEN
	prepare_web_container bats-host-7 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-7
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "X-Forwarded-Port: 1234" -H "Host: web.bats"
	assert_output -l 'X-Forwarded-Port: 1234'
}

##### Other headers

@test "[$TEST_FILE] nginx-proxy generates X-Real-IP" {
	# WHEN
	prepare_web_container bats-host-8 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-8
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Host: web.bats"
	assert_output -p 'X-Real-IP: '
}

@test "[$TEST_FILE] nginx-proxy passes Host" {
	# WHEN
	prepare_web_container bats-host-9 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-9
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Host: web.bats"
	assert_output -l 'Host: web.bats'
}

@test "[$TEST_FILE] nginx-proxy supresses Proxy for httpoxy protection" {
	# WHEN
	prepare_web_container bats-host-10 80 -e VIRTUAL_HOST=web.bats
	dockergen_wait_for_event $SUT_CONTAINER start bats-host-10
	sleep 1

	# THEN
	run curl_container $SUT_CONTAINER /headers -H "Proxy: tcp://foo.com" -H "Host: web.bats"
	refute_output -l 'Proxy: tcp://foo.com'
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}
