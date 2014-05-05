FROM ubuntu:12.04
MAINTAINER Jason Wilder jwilder@litl.com

# Install Nginx.
RUN apt-get update
RUN apt-get install -y python-software-properties wget supervisor
RUN add-apt-repository -y ppa:nginx/stable

RUN apt-get update
RUN apt-get install -y nginx 
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN mkdir /app
WORKDIR /app
ADD . /app

RUN wget https://github.com/jwilder/docker-gen/releases/download/0.1.2/docker-gen-linux-amd64-0.1.2.tar.gz
RUN tar xvzf docker-gen-linux-amd64-0.1.2.tar.gz

RUN mkdir -p /var/log/supervisor
ADD supervisor.conf /etc/supervisor/conf.d/supervisor.conf

EXPOSE 80
ENV DOCKER_HOST unix:///tmp/docker.sock

CMD ["/usr/bin/supervisord"]
