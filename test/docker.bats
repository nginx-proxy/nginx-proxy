#!/usr/bin/env bats
load test_helpers


@test "[$TEST_FILE] start 2 web containers" {
	prepare_web_container bats-web1 81 -e VIRTUAL_HOST=web1.bats
	prepare_web_container bats-web2 82 -e VIRTUAL_HOST=web2.bats
}


@test "[$TEST_FILE] -v /var/run/docker.sock:/tmp/docker.sock:ro" {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-1

	# WHEN nginx-proxy runs on our docker host using the default unix socket
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"

	# THEN
	assert_nginxproxy_behaves $SUT_CONTAINER
}


@test "[$TEST_FILE] -v /var/run/docker.sock:/f00.sock:ro -e DOCKER_HOST=unix:///f00.sock" {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-2

	# WHEN nginx-proxy runs on our docker host using a custom unix socket
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/f00.sock:ro -e DOCKER_HOST=unix:///f00.sock
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"

	# THEN
	assert_nginxproxy_behaves $SUT_CONTAINER
}


@test "[$TEST_FILE] -e DOCKER_HOST=tcp://..." {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-3
	# GIVEN a container exposing our docker host over TCP
	run docker_tcp bats-docker-tcp
	assert_success
	sleep 1s

	# WHEN nginx-proxy runs on our docker host using tcp to connect to our docker host
	run nginxproxy $SUT_CONTAINER -e DOCKER_HOST="tcp://bats-docker-tcp:2375" --link bats-docker-tcp:bats-docker-tcp
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"

	# THEN
	assert_nginxproxy_behaves $SUT_CONTAINER
}


@test "[$TEST_FILE] separated containers (nginx + docker-gen + nginx.tmpl)" {
	docker_clean bats-nginx
	docker_clean bats-docker-gen

	# GIVEN a simple nginx container
	run docker run -d \
		--label bats-type="nginx" \
		--name bats-nginx \
		-v /etc/nginx/conf.d/ \
		-v /etc/nginx/certs/ \
		nginx:latest
	assert_success
	run retry 5 1s docker run --label bats-type="curl" appropriate/curl --silent --fail --head http://$(docker_ip bats-nginx)/
	assert_output -l 0 $'HTTP/1.1 200 OK\r'

	# WHEN docker-gen runs on our docker host
	run docker run -d \
		--label bats-type="docker-gen" \
		--name bats-docker-gen \
		-v /var/run/docker.sock:/tmp/docker.sock:ro \
		-v $BATS_TEST_DIRNAME/../nginx.tmpl:/etc/docker-gen/templates/nginx.tmpl:ro \
		--volumes-from bats-nginx \
		--expose 80 \
		jwilder/docker-gen:0.7.3 \
			-notify-sighup bats-nginx \
			-watch \
			-only-exposed \
			/etc/docker-gen/templates/nginx.tmpl \
			/etc/nginx/conf.d/default.conf
	assert_success
	docker_wait_for_log bats-docker-gen 9 "Watching docker events"

	# Give some time to the docker-gen container to notify bats-nginx so it
	# reloads its config
	sleep 2s

	run docker_running_state bats-nginx
	assert_output "true" || {
		docker logs bats-docker-gen
		false
	} >&2

	# THEN
	assert_nginxproxy_behaves bats-nginx
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}


# $1 nginx-proxy container
function assert_nginxproxy_behaves {
	local -r container=$1

	# Querying the proxy without Host header → 503
	run curl_container $container / --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'

	# Querying the proxy with Host header → 200
	run curl_container $container /port --header "Host: web1.bats"
	assert_output "answer from port 81"

	run curl_container $container /port --header "Host: web2.bats"
	assert_output "answer from port 82"

	# Querying the proxy with unknown Host header → 503
	run curl_container $container /port --header "Host: webFOO.bats" --head
	assert_output -l 0 $'HTTP/1.1 503 Service Temporarily Unavailable\r'
}
