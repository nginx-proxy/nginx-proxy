#!/bin/bash
set -e

function _parse_true() {
	case "$1" in
		
		true | True | TRUE | 1)
		return 0
		;;
		
		*)
		return 1
		;;

	esac
}

function _parse_false() {
	case "$1" in
		
		false | False | FALSE | 0)
		return 0
		;;
		
		*)
		return 1
		;;

	esac
}

function _print_version {
    if [[ -n "${NGINX_PROXY_VERSION:-}" ]]; then
        echo "Info: running nginx-proxy version ${NGINX_PROXY_VERSION}"
    fi
}

function _check_unix_socket() {
	# Warn if the DOCKER_HOST socket does not exist
	if [[ ${DOCKER_HOST} == unix://* ]]; then
		local SOCKET_FILE="${DOCKER_HOST#unix://}"

		if [[ ! -S ${SOCKET_FILE} ]]; then
			cat >&2 <<-EOT
				ERROR: you need to share your Docker host socket with a volume at ${SOCKET_FILE}
				Typically you should run your nginxproxy/nginx-proxy with: \`-v /var/run/docker.sock:${SOCKET_FILE}:ro\`
				See the documentation at: https://github.com/nginx-proxy/nginx-proxy/#usage
			EOT

			exit 1
		fi
	fi
}

function _resolvers() {
	# Compute the DNS resolvers for use in the templates - if the IP contains ":", it's IPv6 and must be enclosed in []
	RESOLVERS=$(awk '$1 == "nameserver" {print ($2 ~ ":")? "["$2"]": $2}' ORS=' ' /etc/resolv.conf | sed 's/ *$//g'); export RESOLVERS

	SCOPED_IPV6_REGEX='\[fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}\]'

	if [[ -z ${RESOLVERS} ]]; then
		echo 'Warning: unable to determine DNS resolvers for nginx' >&2
		unset RESOLVERS
	elif [[ ${RESOLVERS} =~ ${SCOPED_IPV6_REGEX} ]]; then
		echo -n 'Warning: Scoped IPv6 addresses removed from resolvers: ' >&2
		echo "${RESOLVERS}" | grep -Eo "$SCOPED_IPV6_REGEX" | paste -s -d ' ' >&2
		RESOLVERS=$(echo "${RESOLVERS}" | sed -r "s/${SCOPED_IPV6_REGEX}//g" | xargs echo -n); export RESOLVERS
	fi
}

function _setup_dhparam() {
	# DH params will be supplied for nginx here:
	local DHPARAM_FILE='/etc/nginx/dhparam/dhparam.pem'

	# Should be 2048, 3072, or 4096 (default):
	local FFDHE_GROUP="${DHPARAM_BITS:=4096}"

	# DH params may be provided by the user (rarely necessary)
	if [[ -f ${DHPARAM_FILE} ]]; then
		echo 'Warning: A custom dhparam.pem file was provided. Best practice is to use standardized RFC7919 DHE groups instead.' >&2
		return 0
	elif _parse_true "${DHPARAM_SKIP:=false}"; then
		echo 'Skipping Diffie-Hellman parameters setup.'
		return 0
	elif _parse_false "${DHPARAM_GENERATION:=true}"; then
		echo 'Warning: The DHPARAM_GENERATION environment variable is deprecated, please consider using DHPARAM_SKIP set to true instead.' >&2
		echo 'Skipping Diffie-Hellman parameters setup.'
		return 0
	elif [[ ! ${DHPARAM_BITS} =~ ^(2048|3072|4096)$ ]]; then
		echo "ERROR: Unsupported DHPARAM_BITS size: ${DHPARAM_BITS}. Use: 2048, 3072, or 4096 (default)." >&2
		exit 1
	fi

	echo 'Setting up DH Parameters..'

	# Use an existing pre-generated DH group from RFC7919 (https://datatracker.ietf.org/doc/html/rfc7919#appendix-A):
	local RFC7919_DHPARAM_FILE="/app/dhparam/ffdhe${FFDHE_GROUP}.pem"

	# Provide the DH params file to nginx:
	cp "${RFC7919_DHPARAM_FILE}" "${DHPARAM_FILE}"
}

# Run the init logic if the default CMD was provided
if [[ $* == 'forego start -r' ]]; then
	_print_version
	
	_check_unix_socket

	_resolvers

	_setup_dhparam
fi

exec "$@"
