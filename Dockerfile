FROM nginx:1.9.6
MAINTAINER Jason Wilder mail@jasonwilder.com

# Install wget and install/updates certificates
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget \
    git \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

# Get Let's Encrypt client source
#RUN git -C /opt clone https://github.com/letsencrypt/letsencrypt
# Get Let's Encrypt simp_le client source
RUN git -C /opt clone https://github.com/kuba/simp_le.git
# Install letsencrypt
#RUN cd /opt/letsencrypt && ./letsencrypt-auto --help
# Install simp_le
RUN cd /opt/simp_le && ./bootstrap.sh && ./venv.sh
#&& \
#RUN /opt/simp_le/venv.sh
# . venv/bin/activate

# Testing directory
RUN mkdir -p /usr/share/nginx/html/.well-known \
 && touch /usr/share/nginx/html/.well-known/testing

# Configure Nginx and apply fix for very long server names
RUN echo "daemon off;" >> /etc/nginx/nginx.conf \
 && sed -i 's/^http {/&\n    server_names_hash_bucket_size 128;/g' /etc/nginx/nginx.conf

# Install Forego
RUN wget -P /usr/local/bin https://godist.herokuapp.com/projects/ddollar/forego/releases/current/linux-amd64/forego \
 && chmod u+x /usr/local/bin/forego

ENV DOCKER_GEN_VERSION 0.4.2

RUN wget https://github.com/jwilder/docker-gen/releases/download/$DOCKER_GEN_VERSION/docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && tar -C /usr/local/bin -xvzf docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz \
 && rm /docker-gen-linux-amd64-$DOCKER_GEN_VERSION.tar.gz

COPY . /app/
WORKDIR /app/

ENV DOCKER_HOST unix:///tmp/docker.sock

VOLUME ["/etc/nginx/certs"]
VOLUME ["/etc/letsencrypt"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["forego", "start", "-r"]
