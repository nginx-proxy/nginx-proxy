#!/bin/bash
set -e

function _setup_dhparam() {
	echo 'Setting up DH Parameters..'

	# DH params will be supplied for nginx here:
	DHPARAM_FILE='/etc/nginx/dhparam/dhparam.pem'

	# DH params may be provided by the user (rarely necessary),
	# or use an existing pre-generated group from RFC7919, defaulting to 4096-bit:
	if [[ -f ${DHPARAM_FILE} ]]
	then
		echo 'Warning: A custom dhparam.pem file was provided. Best practice is to use standardized RFC7919 DHE groups instead.' >&2
	else
		# ENV DHPARAM_BITS - Defines which RFC7919 DHE group to use (default: 4096-bit):
		local FFDHE_GROUP="${DHPARAM_BITS:-4096}"
		# RFC7919 groups are defined here:
		# https://datatracker.ietf.org/doc/html/rfc7919#appendix-A
		local RFC7919_DHPARAM_FILE="/app/dhparam/ffdhe${FFDHE_GROUP}.pem"

		# Only the following pre-generated sizes are supported,
		# emit an error and kill the container if provided an invalid value:
		if [[ ! ${DHPARAM_BITS} =~ ^(2048|3072|4096)$ ]]
		then
			echo "ERROR: Unsupported DHPARAM_BITS size: ${DHPARAM_BITS}, use 2048, 3072, or 4096 (default)." >&2
			exit 1
		fi

		# Provide the DH params file to nginx:
		cp "${RFC7919_DHPARAM_FILE}" "${DHPARAM_FILE}"
	fi
}

function _init() {
# Warn if the DOCKER_HOST socket does not exist
if [[ $DOCKER_HOST = unix://* ]]; then
	socket_file=${DOCKER_HOST#unix://}
	if ! [ -S "$socket_file" ]; then
		cat >&2 <<-EOT
			ERROR: you need to share your Docker host socket with a volume at $socket_file
			Typically you should run your nginxproxy/nginx-proxy with: \`-v /var/run/docker.sock:$socket_file:ro\`
			See the documentation at http://git.io/vZaGJ
		EOT

		exit 1

	fi
fi

_setup_dhparam

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
}

# Run the init logic if the default CMD was provided
if [[ $* == 'forego start -r' ]]; then
	_init
fi

exec "$@"
