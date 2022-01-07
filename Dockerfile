# setup build arguments for version of dependencies to use
ARG DOCKER_GEN_VERSION=0.7.7
ARG GOREMAN_VERSION=v0.3.8

# Use a specific version of golang to build both binaries
FROM golang:1.16.7 as gobuilder

# Build docker-gen from scratch
FROM gobuilder as dockergen

ARG DOCKER_GEN_VERSION

RUN git clone https://github.com/jwilder/docker-gen \
   && cd /go/docker-gen \
   && git -c advice.detachedHead=false checkout $DOCKER_GEN_VERSION \
   && go mod download \
   && CGO_ENABLED=0 GOOS=linux go build -ldflags "-X main.buildVersion=${DOCKER_GEN_VERSION}" ./cmd/docker-gen \
   && go clean -cache \
   && mv docker-gen /usr/local/bin/ \
   && cd - \
   && rm -rf /go/docker-gen

# Build goreman from scratch
FROM gobuilder as goreman

ARG GOREMAN_VERSION

RUN git clone https://github.com/mattn/goreman/ \
   && cd /go/goreman \
   && git -c advice.detachedHead=false checkout $GOREMAN_VERSION \
   && go mod download \
   && CGO_ENABLED=0 GOOS=linux go build -o goreman . \
   && go clean -cache \
   && mv goreman /usr/local/bin/ \
   && cd - \
   && rm -rf /go/goreman

# Build the final image
FROM nginx:1.21.5
LABEL maintainer="Nicolas Duchon <nicolas.duchon@gmail.com> (@buchdag)"

# Install wget and install/updates certificates
RUN apt-get update \
   && apt-get install -y -q --no-install-recommends \
   ca-certificates \
   wget \
   && apt-get clean \
   && rm -r /var/lib/apt/lists/*


# Configure Nginx and apply fix for very long server names
RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
   && sed -i 's/worker_processes  1/worker_processes  auto/' /etc/nginx/nginx.conf \
   && sed -i 's/worker_connections  1024/worker_connections  10240/' /etc/nginx/nginx.conf \
   && mkdir -p '/etc/nginx/dhparam'

# Install goreman + docker-gen
COPY --from=goreman /usr/local/bin/goreman /usr/local/bin/goreman
COPY --from=dockergen /usr/local/bin/docker-gen /usr/local/bin/docker-gen

# Add DOCKER_GEN_VERSION environment variable
# Because some external projects rely on it
ARG DOCKER_GEN_VERSION
ENV DOCKER_GEN_VERSION=${DOCKER_GEN_VERSION}

COPY network_internal.conf /etc/nginx/

COPY . /app/
WORKDIR /app/

ENV DOCKER_HOST unix:///tmp/docker.sock

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["goreman", "start"]
