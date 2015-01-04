FROM nginx:1.7.8
MAINTAINER Jason Wilder jwilder@litl.com

# Install wget and install/updates certificates
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    ca-certificates \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

# fix for long server names in Nginx
RUN sed -i 's/^http {/&\n    server_names_hash_bucket_size 64;/g' /etc/nginx/nginx.conf

ENV DOCKER_GEN_VERSION 0.3.6

# Install docker-gen
ADD docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz /usr/local/bin

COPY ./root/ /
WORKDIR /app/

ENV DOCKER_HOST unix:///tmp/docker.sock

VOLUME ["/etc/nginx/certs"]

CMD ["forego", "start", "-r"]
