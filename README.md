nginx-proxy sets up a container running nginx and [docker-gen][1].  docker-gen generate reverse proxy configs for nginx and reloads nginx when containers they are started and stop.

See [Automated Nginx Reverse Proxy for Docker][2] for why you might want to use this.

To run it:

    $ docker run -d -p 80:80 -v /var/run/docker.sock:/tmp/docker.sock -t jwilder/nginx-proxy

Then start any containers you want proxied with an env var VIRTUAL_HOST=subdomain.youdomain.com

    $ docker run -e VIRTUAL_HOST=foo.bar.com -t ...

Provided your DNS is setup to forward foo.bar.com to the a host running nginx-proxy, the request will be routed to a container with the VIRTUAL_HOST env var set.

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


  [1]: https://github.com/jwilder/docker-gen
  [2]: http://jasonwilder.com/blog/2014/03/25/automated-nginx-reverse-proxy-for-docker/
