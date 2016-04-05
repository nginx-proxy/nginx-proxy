FROM nginx:alpine
MAINTAINER Jason Wilder mail@jasonwilder.com

# Install wget and install/updates certificates
RUN apk add --no-cache --virtual .run-deps \
    ca-certificates \
    bash

# Configure Nginx and apply fix for very long server names
COPY nginx.conf /etc/nginx/
RUN mkdir /etc/nginx/conf.d

# Install Forego
RUN wget https://github.com/jwilder/forego/releases/download/v0.16.1/forego -O /usr/local/bin/forego \
    && chmod u+x /usr/local/bin/forego
ENV DOCKER_GEN_VERSION 0.7.0

RUN wget https://github.com/jwilder/docker-gen/releases/download/$DOCKER_GEN_VERSION/docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && tar -C /usr/local/bin -xvzf docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && rm /docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz

COPY . /app/
WORKDIR /app/

ENV DOCKER_HOST unix:///tmp/docker.sock

VOLUME ["/etc/nginx/certs"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["forego", "start", "-r"]
