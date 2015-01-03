nginx: nginx
dockergen: docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
dockergen: docker-gen -watch -only-exposed /app/index.html.tmpl /app/www/index.html
