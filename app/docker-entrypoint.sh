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
	# Honor a user-provided RESOLVERS value and only autodetect the DNS resolvers
	# from /etc/resolv.conf when it has not been set (see issue #2699).
	if [[ -n ${RESOLVERS:-} ]]; then
		export RESOLVERS
		return
	fi

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

function _update_cloudflare_real_ip() {
    # Generate /etc/nginx/conf.d/cloudflare.conf if updater exists
    if [[ -x /app/scripts/update-cloudflare-real-ip.sh ]]; then
        # rc 3 = unchanged; on error the existing file (if any) is kept as-is.
        # A file from a previous run already exists: fail fast, cron refreshes it later.
        local rc=0
        if [[ -f /etc/nginx/conf.d/cloudflare.conf ]]; then
            CF_FETCH_RETRIES=0 CF_FETCH_MAX_TIME=10 /app/scripts/update-cloudflare-real-ip.sh || rc=$?
        else
            /app/scripts/update-cloudflare-real-ip.sh || rc=$?
        fi
        if [[ $rc -ne 0 && $rc -ne 3 ]]; then
            echo 'Warning: failed to update Cloudflare real IP configuration, keeping existing one' >&2
        fi
    fi
}

function _setup_cf_cron() {
    # Generate crontab for Cloudflare refresh based on CF_REFRESH_INTERVAL
    local default_schedule
    default_schedule="0 */12 * * *"

    local interval
    interval="${CF_REFRESH_INTERVAL:-${default_schedule}}"

    local schedule
    schedule=""

    # If value looks like a 5-field cron spec, use it as-is (avoid globbing). Otherwise fallback.
    if [ "$(printf '%s\n' "${interval}" | awk '{print NF}')" -eq 5 ]; then
        schedule="${interval}"
    else
        schedule="${default_schedule}"
    fi

    mkdir -p /etc/crontabs
    touch /var/log/cron.log
    {
        echo "${schedule} bash /app/scripts/refresh-cloudflare-and-reload.sh >> /var/log/cron.log 2>&1"
        # Startup fetch failed and there is no file yet: retry every 10 minutes until it exists.
        echo "*/10 * * * * [ -f /etc/nginx/conf.d/cloudflare.conf ] || bash /app/scripts/refresh-cloudflare-and-reload.sh >> /var/log/cron.log 2>&1"
    } > /etc/crontabs/root
}

# Run the init logic if the default CMD was provided
if [[ $* == 'forego start -r' ]] || [[ $* =~ 'docker-gen -watch' ]]; then
	_print_version
	
	_check_unix_socket

	_resolvers

	_setup_dhparam

    _update_cloudflare_real_ip

    _setup_cf_cron

	if [ -z "${TRUST_DOWNSTREAM_PROXY}" ]; then
		cat >&2 <<-EOT
			Warning: TRUST_DOWNSTREAM_PROXY is not set; defaulting to "true". For security, you should explicitly set TRUST_DOWNSTREAM_PROXY to "false" if there is not a trusted reverse proxy in front of this proxy.
			Warning: The default value of TRUST_DOWNSTREAM_PROXY might change to "false" in a future version of nginx-proxy. If you require TRUST_DOWNSTREAM_PROXY to be enabled, explicitly set it to "true".
		EOT
	fi

	# Replace $NGINX_CONTAINER_LABEL in the command line arguments with the actual value of the environment variable
	for ((i=1; i<=$#; i++)); do
		if [[ ${!i} =~ "\$NGINX_CONTAINER_LABEL" && -n "$NGINX_CONTAINER_LABEL" ]]; then
			set -- "${@:1:i-1}" "${!i/\$NGINX_CONTAINER_LABEL/${NGINX_CONTAINER_LABEL}}" "${@:i+1}"
		fi
	done
fi

exec "$@"
