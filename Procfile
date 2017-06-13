dockergen: docker-gen -watch -notify "/app/updatessl.sh updatessl" /app/nginx.tmpl /etc/nginx/conf.d/default.conf
nginx: nginx
cron: cron -f || crond -f