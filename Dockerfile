# setup build arguments for version of dependencies to use
ARG FOREGO_VERSION=v0.17.0

FROM nginxproxy/docker-gen:0.10.4-debian AS docker-gen

# Build forego from scratch
FROM golang:1.20.3 as forego

ARG FOREGO_VERSION

RUN git clone https://github.com/nginx-proxy/forego/ \
   && cd /go/forego \
   && git -c advice.detachedHead=false checkout $FOREGO_VERSION \
   && go mod download \
   && CGO_ENABLED=0 GOOS=linux go build -o forego . \
   && go clean -cache \
   && mv forego /usr/local/bin/ \
   && cd - \
   && rm -rf /go/forego

# Build the final image
FROM nginx:1.23.4

ARG NGINX_PROXY_VERSION
# Add DOCKER_GEN_VERSION environment variable because 
# acme-companion rely on it (but the actual value is not important)
ARG DOCKER_GEN_VERSION="unknown"
ENV NGINX_PROXY_VERSION=${NGINX_PROXY_VERSION} \
   DOCKER_GEN_VERSION=${DOCKER_GEN_VERSION} \
   DOCKER_HOST=unix:///tmp/docker.sock

# Install/update certificates
RUN apt-get update \
   && apt-get install -y -q --no-install-recommends ca-certificates \
   && apt-get clean \
   && rm -r /var/lib/apt/lists/*


# Configure Nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
   && sed -i 's/worker_processes  1/worker_processes  auto/' /etc/nginx/nginx.conf \
   && sed -i 's/worker_connections  1024/worker_connections  10240/' /etc/nginx/nginx.conf \
   && mkdir -p '/etc/nginx/dhparam'

# Install Forego + docker-gen
COPY --from=forego /usr/local/bin/forego /usr/local/bin/forego
COPY --from=docker-gen /usr/local/bin/docker-gen /usr/local/bin/docker-gen

COPY network_internal.conf /etc/nginx/

COPY app nginx.tmpl LICENSE /app/
WORKDIR /app/

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["forego", "start", "-r"]
