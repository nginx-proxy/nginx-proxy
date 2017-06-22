#!/bin/bash
###############################################################################
#
# Signals:
#   - HUP: reload docker-gen
#   - USR1: reload nginx
#
###############################################################################
set -u

function start_docker_gen {
    echo "~~~~~ Starting docker-gen ~~~~~"
    {
        while true; do
            docker-gen -watch -notify "kill -USR1 1" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
            echo "docker-gen exited"
            echo "~~~~~ Restarting docker-gen ~~~~~~"
        done
    } &
}

function start_nginx {
    echo "~~~~~ Starting nginx ~~~~~"
    {
        while true; do
            nginx
            echo "nginx exited, checking config..."
            if nginx -t; then
                echo "~~~~~ Restarting nginx ~~~~~~"
            else
                exit 1
            fi
        done
    } &
}


function reload_nginx {
    if pgrep nginx >/dev/null; then
        # nginx is already running
        echo "~~~~~ Reloading nginx ~~~~~"
        pkill -HUP nginx
    else
        start_nginx
    fi
}

###############################################################################

function handle_SIGHUP {
    echo "~~~~~ Signal HUP received ~~~~~"
    if ! pgrep nginx >/dev/null; then
        echo "~~~~~ Starting nginx ~~~~~"
        nginx &
    fi
    pkill -HUP docker-gen  # forward SIGHUP to docker-gen
    wait
}

function handle_SIGUSR1 {
    echo "~~~~~ Signal USR1 received ~~~~~"
    reload_nginx
    wait
}

###############################################################################

# If the user has run provided a command, run it instead
if [ $# -ne 0 ]; then
	exec "$@"
fi

cat <<-OEBANNER
    ███╗   ██╗ ██████╗ ██╗███╗   ██╗██╗  ██╗     ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
    ████╗  ██║██╔════╝ ██║████╗  ██║╚██╗██╔╝     ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
    ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║ ╚███╔╝█████╗██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝
    ██║╚██╗██║██║   ██║██║██║╚██╗██║ ██╔██╗╚════╝██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝
    ██║ ╚████║╚██████╔╝██║██║ ╚████║██╔╝ ██╗     ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║
    ╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝     ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝
OEBANNER


# Error if the DOCKER_HOST socket does not exist
if [[ $DOCKER_HOST == unix://* ]]; then
	socket_file=${DOCKER_HOST#unix://}
	if ! [ -S $socket_file ]; then
		cat >&2 <<-EOT
			ERROR: you need to share your Docker host socket with a volume at $socket_file
			Typically you should run your jwilder/nginx-proxy with: \`-v /var/run/docker.sock:$socket_file:ro\`
			See the documentation at http://git.io/vZaGJ
		EOT
		exit 1
	fi
fi


trap handle_SIGHUP HUP
trap handle_SIGUSR1 USR1
trap "exit 0" TERM

rm /etc/nginx/conf.d/default.conf
start_docker_gen
wait