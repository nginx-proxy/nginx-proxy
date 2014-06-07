FROM ubuntu:12.04
MAINTAINER Jason Wilder jwilder@litl.com

# Install Nginx.
RUN apt-get update
RUN apt-get install -y python-software-properties wget
RUN add-apt-repository -y ppa:nginx/stable

RUN apt-get update
RUN apt-get install -y nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

#fix for long server names
RUN sed -i 's/# server_names_hash_bucket/server_names_hash_bucket/g' /etc/nginx/nginx.conf

RUN mkdir /app
WORKDIR /app
ADD . /app

RUN wget https://github.com/jwilder/forego/releases/download/v0.8.3-p2/forego-v0.8.3-p2-linux-amd64.tar.gz
RUN tar xvzf forego-v0.8.3-p2-linux-amd64.tar.gz && mv forego /usr/local/bin && rm forego-v0.8.3-p2-linux-amd64.tar.gz

RUN wget https://github.com/jwilder/docker-gen/releases/download/0.2.1/docker-gen-linux-amd64-0.2.1.tar.gz
RUN tar xvzf docker-gen-linux-amd64-0.2.1.tar.gz

EXPOSE 80
ENV DOCKER_HOST unix:///tmp/docker.sock

CMD ["forego", "start", "-r"]
