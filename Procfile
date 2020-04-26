swarmmerge: while true; do ls -d /etc/nginx/node.conf.d/*.conf | entr -d python3 /app/mergeswarm.py; done
dockergen: docker-gen -watch /app/nginx.tmpl /etc/nginx/node.conf.d/`hostname`.conf
nginx: nginx
