Nginx proxy test suite
======================

Install requirements
--------------------

You need [Docker Compose v2](https://docs.docker.com/compose/install/linux/), [python 3.9](https://www.python.org/) and [pip](https://pip.pypa.io/en/stable/installation/)  installed. Then run the commands:

    pip install -r requirements/python-requirements.txt

Prepare the nginx-proxy test image
----------------------------------

    make build-nginx-proxy-test-debian

or if you want to test the alpine flavor:

    make build-nginx-proxy-test-alpine

Run the test suite
------------------

    pytest

need more verbosity ?

    pytest -s

Note: By default this test suite relies on Docker Compose v2 with the command `docker compose`. It still supports Docker Compose v1 via the `DOCKER_COMPOSE` environment variable:

    DOCKER_COMPOSE=docker-compose pytest

Run one single test module
--------------------------

    pytest test_nominal.py

Run the test suite from a Docker container
------------------------------------------

If you cannot (or don't want to) install pytest and its requirements on your computer. You can use the nginx-proxy-tester docker image to run the test suite from a Docker container.

    make test-debian

or if you want to test the alpine flavor:

    make test-alpine

Write a test module
-------------------

This test suite uses [pytest](http://doc.pytest.org/en/latest/). The [conftest.py](conftest.py) file will be automatically loaded by pytest and will provide you with two useful pytest [fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html): 

- docker_compose
- nginxproxy


### docker_compose fixture

When using the `docker_compose` fixture in a test, pytest will try to start the [Docker Compose](https://docs.docker.com/compose/) services corresponding to the current test module, based on the test module filename.

By default, if your test module file is `test/test_subdir/test_example.py`, then the `docker_compose` fixture will try to load the following files, [merging them](https://docs.docker.com/reference/compose-file/merge/) in this order:

1. `test/compose.base.yml`
2. `test/test_subdir/compose.base.override.yml` (if it exists)
3. `test/test_subdir/test_example.yml`

The fixture will run the _docker compose_ command with the `-f` option to load the given compose files. So you can test your docker compose file syntax by running it yourself with:

    docker compose -f test/compose.base.yml -f test/test_subdir/test_example.yml up -d

The first file contains the base configuration of the nginx-proxy container common to most tests:

```yaml
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy:test
    container_name: nginx-proxy
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
    ports:
      - "80:80"
      - "443:443"
```

The second optional file allow you to override this base configuration for all test modules in a subfolder.

The third file contains the services and overrides specific to a given test module.

This automatic merge can be bypassed by using a file named `test_example.base.yml` (instead of `test_example.yml`). When this file exist, it will be the only one used by the test and no merge with other compose files will automatically occur.

The `docker_compose` fixture also set the `PYTEST_MODULE_PATH` environment variable to the absolute path of the current test module directory, so it can be used to mount files or directory relatives to the current test.

In the case you are running pytest from within a docker container, the `docker_compose` fixture will make sure the container running pytest is attached to all docker networks. That way, your test will be able to reach any of them.

In your tests, you can use the `docker_compose` variable to query and command the docker daemon as it provides you with a [client from the docker python module](https://docker-py.readthedocs.io/en/4.4.4/client.html#client-reference).

Also this fixture alters the way the python interpreter resolves domain names to IP addresses in the following ways:

Any domain name containing the substring `nginx-proxy` will resolve to `127.0.0.1` if the tests are executed on a Darwin (macOS) system, otherwise the IP address of the container that was created from the `nginxproxy/nginx-proxy:test` image.

So, in tests, all the following domain names will resolve to either localhost or the nginx-proxy container's IP:

- `nginx-proxy`
- `nginx-proxy.com`
- `www.nginx-proxy.com`
- `www.nginx-proxy.test`
- `www.nginx-proxy`
- `whatever.nginx-proxyooooooo`
- ...

Any domain name ending with `XXX.container.docker` will resolve to `127.0.0.1` if the tests are executed on a Darwin (macOS) system, otherwise the IP address of the container named `XXX`.

So, on a non-Darwin system:

- `web1.container.docker` will resolve to the IP address of the `web1` container
- `f00.web1.container.docker` will resolve to the IP address of the `web1` container
- `anything.whatever.web2.container.docker` will resolve to the IP address of the `web2` container

Otherwise, domain names are resoved as usual using your system DNS resolver.

### nginxproxy fixture

The `nginxproxy` fixture will provide you with a replacement for the python [requests](https://pypi.python.org/pypi/requests/) module. This replacement will just repeat up to 30 times a requests if it receives the HTTP error 404 or 502. This error occurs when you try to send queries to nginx-proxy too early after the container creation.

Also this requests replacement is preconfigured to use the Certificate Authority root certificate [certs/ca-root.crt](certs/) to validate https connections.

Furthermore, the nginxproxy methods accept an additional keyword parameter: `ipv6` which forces requests made against containers to use the containers IPv6 address when set to `True`. If IPv6 is not supported by the system or docker, that particular test will be skipped.

    def test_forwards_to_web1_ipv6(docker_compose, nginxproxy):
        r = nginxproxy.get("http://web1.nginx-proxy.tld/port", ipv6=True)
        assert r.status_code == 200   
        assert r.text == "answer from port 81\n"



### The web docker image

When you run the `make build-webserver` command, you built a [`web`](requirements/README.md) docker image which is convenient for running a small web server in a container. This image can produce containers that listens on multiple ports at the same time.

### Testing TLS

If you need to create server certificates, use the [`certs/create_server_certificate.sh`](certs/) script. Pytest will be able to validate any certificate issued from this script.
