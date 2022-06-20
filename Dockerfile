# setup build arguments for version of dependencies to use
ARG DOCKER_GEN_VERSION=0.9.0
ARG FOREGO_VERSION=v0.17.0

# Use a specific version of golang to build both binaries
FROM golang:1.18.1 as gobuilder

# Build docker-gen from scratch
FROM gobuilder as dockergen

ARG DOCKER_GEN_VERSION

RUN git clone https://github.com/nginx-proxy/docker-gen \
   && cd /go/docker-gen \
   && git -c advice.detachedHead=false checkout $DOCKER_GEN_VERSION \
   && go mod download \
   && CGO_ENABLED=0 GOOS=linux go build -ldflags "-X main.buildVersion=${DOCKER_GEN_VERSION}" ./cmd/docker-gen \
   && go clean -cache \
   && mv docker-gen /usr/local/bin/ \
   && cd - \
   && rm -rf /go/docker-gen

# Build forego from scratch
FROM gobuilder as forego

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


# Build headers more module from scratch
FROM nginx:1.21.6 AS headers-more-nginx-module

# nginx:alpine contains NGINX_VERSION environment variable, like so:
# ENV NGINX_VERSION 1.15.0
ARG HEADERS_MORE_VERSION=v0.33

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        libpcre++-dev \
        zlib1g-dev \
        libgeoip-dev \
        wget \
        git
# Download sources
RUN wget "http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz" -O nginx.tar.gz

RUN cd /opt \
    && git clone --depth 1 -b $HEADERS_MORE_VERSION --single-branch https://github.com/openresty/headers-more-nginx-module.git \
    && cd /opt/headers-more-nginx-module \
    && git submodule update --init \
    && cd /opt \
    && wget -O - http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz | tar zxfv - \
    && mv /opt/nginx-$NGINX_VERSION /opt/nginx \
    && cd /opt/nginx \
    && ./configure --with-compat --add-dynamic-module=/opt/headers-more-nginx-module \
    && make modules 

# Build the final image
FROM nginx:1.21.6

ARG NGINX_PROXY_VERSION
# Add DOCKER_GEN_VERSION environment variable
# Because some external projects rely on it
ARG DOCKER_GEN_VERSION
ENV NGINX_PROXY_VERSION=${NGINX_PROXY_VERSION} \
   DOCKER_GEN_VERSION=${DOCKER_GEN_VERSION} \
   DOCKER_HOST=unix:///tmp/docker.sock

# Copy more filter modules to the image
COPY --from=headers-more-nginx-module /opt/nginx/objs/ngx_http_headers_more_filter_module.so /usr/lib/nginx/modules
RUN chmod -R 644 \
        /usr/lib/nginx/modules/ngx_http_headers_more_filter_module.so \
    && sed -i '1iload_module \/usr\/lib\/nginx\/modules\/ngx_http_headers_more_filter_module.so;' /etc/nginx/nginx.conf 

# Install wget and install/updates certificates
RUN apt-get update \
   && apt-get install -y -q --no-install-recommends \
   ca-certificates \
   wget \
   && apt-get clean \
   && rm -r /var/lib/apt/lists/*


# Configure Nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
   && sed -i 's/worker_processes  1/worker_processes  auto/' /etc/nginx/nginx.conf \
   && sed -i 's/worker_connections  1024/worker_connections  10240/' /etc/nginx/nginx.conf \
   && mkdir -p '/etc/nginx/dhparam'

# Install Forego + docker-gen
COPY --from=forego /usr/local/bin/forego /usr/local/bin/forego
COPY --from=dockergen /usr/local/bin/docker-gen /usr/local/bin/docker-gen

COPY network_internal.conf /etc/nginx/

COPY app nginx.tmpl LICENSE /app/
WORKDIR /app/

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["forego", "start", "-r"]
