This directory contains resources to build Docker images tests depend on

# Build images

    ./build.sh   


# python-requirements.txt

If you want to run the test suite from your computer, you need python and a few python modules.
The _python-requirements.txt_ file describes the python modules required. To install them, use
pip:

    pip install -r python-requirements.txt

If you don't want to run the test from your computer, you can run the tests from a docker container, see the _pytest.sh_ script.


# Images

## web

This container will run one or many webservers, each of them listening on a single port.

Ports are specified using the `WEB_PORTS` environment variable:

    docker run -d -e WEB_PORTS=80 web  # will create a container running one webserver listening on port 80
    docker run -d -e WEB_PORTS="80 81" web  # will create a container running two webservers, one listening on port 80 and a second one listening on port 81

The webserver answers on two paths:

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


## nginx-proxy-tester

This is an optional requirement which is usefull if you cannot (or don't want to) install pytest and its requirements on your computer. In this case, you can use the `nginx-proxy-tester` docker image to run the test suite from a Docker container.

To use this image, it is mandatory to run the container using the `pytest.sh` shell script. The script will build the image and run a container from it with the appropriate volumes and settings.
