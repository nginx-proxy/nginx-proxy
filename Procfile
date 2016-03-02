nginx: while [ ! -f /etc/nginx/conf.d/dockergen.conf ]; do echo "Waiting for dockergen.conf to appear before starting nginx..."; sleep 1; done; echo "Starting nginx..."; nginx
dockergen: echo "Starting docker-gen..."; docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/dockergen.conf
