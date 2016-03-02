nginx: sleep 2; echo "Starting nginx..."; nginx
dockergen: echo "Starting docker-gen..."; docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
