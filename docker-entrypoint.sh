#!/bin/bash
set -e

check_unix_socket() {
	if [[ $DOCKER_HOST == unix://* ]]; then
		socket_file=${DOCKER_HOST#unix://}
		if ! [ -S $socket_file ]; then
			cat >&2 <<-EOT
				ERROR: you need to share your docker host socket with a volume at $socket_file
				Typically you should run your jwilder/nginx-proxy with: \`-v /var/run/docker.sock:$socket_file:ro\`
				See documentation at http://git.io/vZaGJ
			EOT
			exit 1
		fi
	fi
}

################################################################################

# check for the expected command
if [ "$1" = 'nginx-proxy' ]; then
	check_unix_socket
	exec forego start -r
fi

# else default to run whatever the user wanted like "bash"
exec "$@"


