#!/usr/bin/env bats

load test_helpers
SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}

function setup {
  stop_bats_containers web
}

@test "[$TEST_FILE] start a nginx-proxy container" {
  run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
  assert_success
  docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"
}

@test "[$TEST_FILE] nginx-proxy can put a container at a specific path" {
	#WHEN a container is run with VIRTUAL_PATH set
	prepare_web_container bats-virtual-path-1 80 -e VIRTUAL_HOST=virtual-path-1.bats -e VIRTUAL_PATH=/virtual_path
	dockergen_wait_for_event $SUT_CONTAINER start bats-virtual-path-1
	sleep 1

	#THEN querying the root -> 404
	run curl_container $SUT_CONTAINER / --head --header "Host: virtual-path-1.bats"
	assert_output -l 0 $'HTTP/1.1 404 Not Found\r'

	#THEN querying an unmatched path -> 503
	run curl_container $SUT_CONTAINER /some_other_path --head --header "Host: virtual-path-1.bats"
	assert_output -l 0 $'HTTP/1.1 404 Not Found\r'

	#THEN
	run curl_container $SUT_CONTAINER /virtual_path/data --header "Host: virtual-path-1.bats"
	assert_output "answer from port 80"
}

@test "[$TEST_FILE] nginx-proxy can put a container at the root" {
	#WHEN a container is run with VIRTUAL_PATH set to /
	prepare_web_container bats-virtual-path-1 80 -e VIRTUAL_HOST=virtual-path-1.bats -e VIRTUAL_PATH=/
	dockergen_wait_for_event $SUT_CONTAINER start bats-virtual-path-1
	sleep 1

	#THEN 
	run curl_container $SUT_CONTAINER /data --header "Host: virtual-path-1.bats"
	assert_output "answer from port 80"
}

@test "[$TEST_FILE] nginx-proxy can put multiple containers at different paths" {
	#WHEN a multiple containers are run with VIRTUAL_PATH set
	prepare_web_container bats-virtual-path-1 80 -e VIRTUAL_HOST=virtual-path-1.bats -e VIRTUAL_PATH=/at-80
	prepare_web_container bats-virtual-path-2 90 -e VIRTUAL_HOST=virtual-path-1.bats -e VIRTUAL_PATH=/at-90
	prepare_web_container bats-virtual-path-3 100 -e VIRTUAL_HOST=virtual-path-1.bats -e VIRTUAL_PATH=/
	dockergen_wait_for_event $SUT_CONTAINER start bats-virtual-path-1
	sleep 1

	#THEN 
	run curl_container $SUT_CONTAINER /data --header "Host: virtual-path-1.bats"
	assert_output "answer from port 100"
	
	#THEN 
	run curl_container $SUT_CONTAINER /at-80/data --header "Host: virtual-path-1.bats"
	assert_output "answer from port 80"
	
	#THEN 
	run curl_container $SUT_CONTAINER /at-90/data --header "Host: virtual-path-1.bats"
	assert_output "answer from port 90"
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}
