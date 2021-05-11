#!/bin/bash
set -e

# Warn if the DOCKER_HOST socket does not exist
if [[ $DOCKER_HOST = unix://* ]]; then
	socket_file=${DOCKER_HOST#unix://}
	if ! [ -S "$socket_file" ]; then
		cat >&2 <<-EOT
			ERROR: you need to share your Docker host socket with a volume at $socket_file
			Typically you should run your nginxproxy/nginx-proxy with: \`-v /var/run/docker.sock:$socket_file:ro\`
			See the documentation at http://git.io/vZaGJ
		EOT
		socketMissing=1
	fi
fi

# Generate dhparam file if required
/app/generate-dhparam.sh

# Compute the DNS resolvers for use in the templates - if the IP contains ":", it's IPv6 and must be enclosed in []
RESOLVERS=$(awk '$1 == "nameserver" {print ($2 ~ ":")? "["$2"]": $2}' ORS=' ' /etc/resolv.conf | sed 's/ *$//g'); export RESOLVERS

SCOPED_IPV6_REGEX="\[fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}\]"

if [ "$RESOLVERS" = "" ]; then
	echo "Warning: unable to determine DNS resolvers for nginx" >&2
	unset RESOLVERS
elif [[ $RESOLVERS =~ $SCOPED_IPV6_REGEX ]]; then
	echo -n "Warning: Scoped IPv6 addresses removed from resolvers: " >&2
	echo "$RESOLVERS" | grep -Eo "$SCOPED_IPV6_REGEX" | paste -s -d ' ' >&2
	RESOLVERS=$(echo "$RESOLVERS" | sed -r "s/$SCOPED_IPV6_REGEX//g" | xargs echo -n); export RESOLVERS
fi

# If the user has run the default command and the socket doesn't exist, fail
if [ "$socketMissing" = 1 ] && [ "$1" = forego ] && [ "$2" = start ] && [ "$3" = '-r' ]; then
	exit 1
fi

exec "$@"
