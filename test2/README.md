Nginx proxy test suite
======================

Install requirements
--------------------

You need [python 2.7](https://www.python.org/) and [pip](https://pip.pypa.io/en/stable/installing/) installed. Then run the commands:

    requirements/build.sh
    pip install -r requirements/python-requirements.txt

If you can't install those requirements on your computer, you can alternatively use the _nginx-proxy-tester.sh_ script which will run the tests from a Docker container which has those requirements.


Prepare the nginx-proxy test image
----------------------------------

    docker build -t jwilder/nginx-proxy:test ..

make sure to tag that test image exactly `jwilder/nginx-proxy:test` or the test suite won't work.


Run the test suite
------------------

    pytest

need more verbosity ?

    pytest -s


Run one single test module
--------------------------

    pytest test_nominal.py


Write a test module
-------------------

This test suite uses [pytest](http://doc.pytest.org/en/latest/). The [conftest.py](conftest.py) file will be automatically loaded by pytest and will provide you with two useful pytest [fixtures](http://doc.pytest.org/en/latest/fixture.html#fixture): 

- docker_compose
- nginxproxy

Also _conftest.py_ alters the way the python interpreter resolves domain names to IP addresses in such a way that any domain name containing the substring `nginx-proxy` will resolve to the IP address of the container that was created from the `jwilder/nginx-proxy:test` image.

So all the following domain names will resolve to the nginx-proxy container in tests:
- `nginx-proxy`
- `nginx-proxy.com`
- `www.nginx-proxy.com`
- `www.nginx-proxy.test`
- `www.nginx-proxy`
- `whatever.nginx-proxyooooooo`
- ...


### docker_compose fixture

When using the `docker_compose` fixture in a test, pytest will try to find a yml file named after your test module filename. For instance, if your test module is `test_example.py`, then the `docker_compose` fixture will try to load a `test_example.yml` [docker compose file](https://docs.docker.com/compose/compose-file/).

The only requirement within that compose file is to have a container declared from the docker image `jwilder/nginx-proxy:test`.

Once the docker compose file found, the fixture will remove all containers, run `docker-compose up`, and finally your test will be executed.

The fixture will run the _docker-compose_ command with the `-f` option to load the given compose file. So you can test your docker compose file syntax by running it yourself with:

    docker-compose -f test_example.yml up -d


### nginxproxy fixture

The `nginxproxy` fixture will provide you with a replacement for the python [requests](https://pypi.python.org/pypi/requests/) module. This replacement will just repeat up to 30 times a requests if it receives the HTTP error 404 or 502. This error occurs when you try to send queries to nginx-proxy too early after the container creation.

Also this requests replacement is preconfigured to use the Certificate Authority root certificate [certs/ca-root.crt](certs/) to validate https connections.


### The web docker image

When you ran the `requirements/build.sh` script earlier, you built a [`web`](requirements/README.md) docker image which is convenient for running a small web server in a container. This image can produce containers that listens on multiple ports at the same time.


### Testing TLS

If you need to create server certificates, use the [`certs/create_server_certificate.sh`](certs/) script. Pytest will be able to validate any certificate issued from this script.