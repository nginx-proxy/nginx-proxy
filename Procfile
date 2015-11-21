nginx: nginx
dockergen: docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
letsencrypt_dockergen: docker-gen -watch -only-exposed /app/letsencrypt_service_data.tmpl /app/letsencrypt_service_data
letsencrypt: /app/letsencrypt_service
