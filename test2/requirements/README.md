This directory contains ressources to build Docker images tests depend on

# Build images

    ./build.sh   


# Images

## web

This container will run one or many webservers, each of them listening on a single port.

Ports are specified using the `WEB_PORTS` environment variable:

    docker run -d -e WEB_PORTS=80 web  # will create a container running one webserver listening on port 80
    docker run -d -e WEB_PORTS="80 81" web  # will create a container running two webservers, one listening on port 80 and a second one listening on port 81

The webserver answer for two paths:

- `/headers`
- `/port`

```
$ docker run -d -e WEB_PORTS=80 -p 80:80 web
$ curl http://127.0.0.1:80/headers
Host: 127.0.0.1
User-Agent: curl/7.47.0
Accept: */*

$ curl http://127.0.0.1:80/port
answer from port 80

```

