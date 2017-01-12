#!/usr/bin/env bats
load test_helpers

function setup {
	# make sure to stop any web container before each test so we don't
	# have any unexpected contaiener running with VIRTUAL_HOST or VIRUTAL_PORT set
	stop_bats_containers web
}

@test "[$TEST_FILE] test dhparam.pem is generated if missing" {
    SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-1

    # WHEN
    run docker_clean $SUT_CONTAINER \
    && docker run -d \
        --label bats-type="nginx-proxy" \
        --name $SUT_CONTAINER \
        -v /var/run/docker.sock:/tmp/docker.sock:ro \
        -e DHPARAM=256 \
        $SUT_IMAGE \
    && wait_for_nginxproxy_container_to_start $SUT_CONTAINER \
    && docker logs $SUT_CONTAINER

    DEFAULT_HASH=$(docker exec $SUT_CONTAINER md5sum /etc/nginx/dhparam/dhparam.pem | cut -d" " -f1)

    assert_success
    docker_wait_for_log $SUT_CONTAINER 30 "Generating DH parameters"

    # THEN
    docker_wait_for_log $SUT_CONTAINER 240 "dhparam generation complete, reloading nginx"

    run docker exec $SUT_CONTAINER md5sum /etc/nginx/dhparam/dhparam.pem
    refute_output -p $DEFAULT_HASH
}

@test "[$TEST_FILE] test dhparam.pem is generated if default one is present" {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-2

	# Copy the default dhparams to a volume and mount it in to ensure it's regenerated
	TMP_DIR=/tmp/nginx-proxy-bats
	if [ ! -d $TMP_DIR ]; then
		mkdir $TMP_DIR
	fi

	# If the previous test crashed, a dhparam is left that only root can delete, so we 
	#  delete it from within a container as root
	if [ -f $TMP_DIR/dhparam.pem ]; then
		docker run --rm -v $TMP_DIR:/opt busybox rm /opt/dhparam.pem
	fi

	cp $DIR/../dhparam.pem.default $TMP_DIR/dhparam.pem

	# WHEN
	run docker_clean $SUT_CONTAINER \
	&& docker run -d \
		--label bats-type="nginx-proxy" \
		--name $SUT_CONTAINER \
		-v /var/run/docker.sock:/tmp/docker.sock:ro \
		-v $TMP_DIR:/etc/nginx/dhparam \
        -e DHPARAM=256 \
		$SUT_IMAGE \
	&& wait_for_nginxproxy_container_to_start $SUT_CONTAINER \
	&& docker logs $SUT_CONTAINER

	# THEN
	assert_success
	docker_wait_for_log $SUT_CONTAINER 30 "Generating DH parameters"

	docker exec $SUT_CONTAINER rm -rf /etc/nginx/dhparam/*
}

@test "[$TEST_FILE] test dhparam.pem is not generated if custom one is present" {
	SUT_CONTAINER=bats-nginx-proxy-${TEST_FILE}-3

	# WHEN
	run nginxproxy $SUT_CONTAINER -v /var/run/docker.sock:/tmp/docker.sock:ro
	assert_success
	docker_wait_for_log $SUT_CONTAINER 9 "Watching docker events"

	# THEN
	run docker exec $SUT_CONTAINER ps aux
	refute_output -p "openssl"
}

@test "[$TEST_FILE] stop all bats containers" {
	stop_bats_containers
}
