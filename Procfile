nginx: nginx
gennginx: docker-gen -watch -only-exposed -notify "nginx -s reload" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
genindex: docker-gen -watch -only-exposed /app/index.tmpl /usr/share/nginx/html/index.html
