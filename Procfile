nginx: nginx
dockergen: /app/docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/sites-enabled/default
