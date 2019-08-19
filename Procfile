htpasswdgen: docker-gen -watch -notify "/app/htpasswd_generator.sh" /app/htpasswd_generator.tmpl /app/htpasswd_generator.sh
dockergen: docker-gen -watch -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
nginx: nginx
