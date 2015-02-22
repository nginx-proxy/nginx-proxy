FROM nginx:1.7.8
MAINTAINER https://m-ko-x.de Markus Kosmal <code@m-ko-x.de>

# set max size within a body
ENV GLOB_MAX_BODY_SIZE "10m"
# set default msg set within basic auth msg
ENV GLOB_AUTH_MSG "Restricted :"
# set default session timeout
ENV GLOB_SSL_SESSION_TIMEOUT "5m"
# default return code for errors
ENV GLOB_HTTP_NO_SERVICE "503"

# enable some kind of prefix redirection
ENV AUTO_REDIRECT_WITH_PREFIX_ENABLED false
# set prefix to be used for auto redirect
ENV AUTO_REDIRECT_PREFIX "www"
# set direction
# - 0: redirect from prefix to non-prefix
# - 1: redirect from non-prefix to prefix
ENV AUTO_REDIRECT_DIRECTION 0

# install packages
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

# Configure Nginx and apply fix for very long server names
RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
 && sed -i 's/^http {/&\n    server_names_hash_bucket_size 128;/g' /etc/nginx/nginx.conf
 
 # Install Forego
RUN wget -P /usr/local/bin https://godist.herokuapp.com/projects/ddollar/forego/releases/current/linux-amd64/forego \
 && chmod u+x /usr/local/bin/forego

ENV DOCKER_GEN_VERSION 0.3.6

RUN wget https://github.com/jwilder/docker-gen/releases/download/$DOCKER_GEN_VERSION/docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && tar -C /usr/local/bin -xvzf docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && rm /docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz

COPY . /app/
WORKDIR /app/

ENV DOCKER_HOST unix:///tmp/docker.sock

VOLUME ["/etc/nginx/certs"]

CMD ["forego", "start", "-r"]
