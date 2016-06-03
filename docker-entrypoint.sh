#!/bin/bash
set -e

# Warn if the DOCKER_HOST socket does not exist
if [[ $DOCKER_HOST == unix://* ]]; then
	socket_file=${DOCKER_HOST#unix://}
	if ! [ -S $socket_file ]; then
		cat >&2 <<-EOT
			ERROR: you need to share your Docker host socket with a volume at $socket_file
			Typically you should run your jwilder/nginx-proxy with: \`-v /var/run/docker.sock:$socket_file:ro\`
			See the documentation at http://git.io/vZaGJ
		EOT
		socketMissing=1
	fi
fi

# If the user has run the default command and the socket doesn't exist, fail
if [ "$socketMissing" = 1 -a "$1" = forego -a "$2" = start -a "$3" = '-r' ]; then
	exit 1
fi

# if a custom template has not been specified
if [ -z "$CUSTOM_TEMPLATE" ]; then
	# try to copy default config to another file if the other file doesn't yet exist
	cp -n nginx.tmpl nginx_default.tmpl

	# create symlink to default config file
	ln -sf nginx_default.tmpl nginx.tmpl
else
	# try to copy default config to another file if the other file doesn't yet exist
	cp -n nginx.tmpl nginx_default.tmpl

	# create symlink to custom config file
	ln -sf $CUSTOM_TEMPLATE nginx.tmpl
fi

exec "$@"
