## functions to help deal with docker

# Removes container $1
function docker_clean {
	docker kill $1 &>/dev/null ||:
	sleep .25s
	docker rm -vf $1 &>/dev/null ||:
	sleep .25s
}

# get the ip of docker container $1
function docker_ip {
	docker inspect --format '{{ .NetworkSettings.IPAddress }}' $1
}

# get the running state of container $1
# → true/false
# fails if the container does not exist
function docker_running_state {
	docker inspect -f {{.State.Running}} $1
}

# get the docker container $1 PID
function docker_pid {
	docker inspect --format {{.State.Pid}} $1
}

# asserts logs from container $1 contains $2
function docker_assert_log {
	local -r container=$1
	shift
	run docker logs $container
	assert_output -p "$*"
}

# wait for a container to produce a given text in its log
# $1 container
# $2 timeout in second
# $* text to wait for
function docker_wait_for_log {
	local -r container=$1
	local -ir timeout_sec=$2
	shift 2
	retry $(( $timeout_sec * 2 )) .5s docker_assert_log $container "$*"
}

# Create a docker container named $1 which exposes the docker host unix 
# socket over tcp on port 2375.
#
# $1 container name
function docker_tcp {
	local container_name="$1"
	docker_clean $container_name
	docker run -d \
		--name $container_name \
		--expose 2375 \
		-v /var/run/docker.sock:/var/run/docker.sock \
		rancher/socat-docker
	docker run --link "$container_name:docker" docker:1.7 version
}
