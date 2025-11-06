FROM nginxproxy/nginx-proxy:alpine

COPY nginx.tmpl /app/nginx.tmpl

RUN chmod 644 /app/nginx.tmpl
