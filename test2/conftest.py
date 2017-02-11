from __future__ import print_function
import json
import logging
import os
import shlex
import socket
import subprocess
import time

import backoff
import docker
import pytest
import requests

logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').setLevel(logging.INFO)
logging.getLogger('patched DNS').setLevel(logging.INFO)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

CA_ROOT_CERTIFICATE = os.path.join(os.path.dirname(__file__), 'certs/ca-root.crt')
I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER = os.path.isfile("/.dockerenv")

docker_client = docker.from_env()


###############################################################################
# 
# utilities
# 
###############################################################################


class requests_for_docker(object):
    """
    Proxy for calling methods of the requests module. 
    When a HTTP response failed due to HTTP Error 404 or 502, retry a few times.
    Provides method `get_conf` to extract the nginx-proxy configuration content.
    """
    def __init__(self):
        self.session = requests.Session()
        if os.path.isfile(CA_ROOT_CERTIFICATE):
            self.session.verify = CA_ROOT_CERTIFICATE

    def get_conf(self):
        """
        Return the nginx config file
        """
        nginx_proxy_containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
        if len(nginx_proxy_containers) > 1:
            pytest.failed("Too many running jwilder/nginx-proxy:test containers")
        elif len(nginx_proxy_containers) == 0:
            pytest.failed("No running jwilder/nginx-proxy:test container")
        return get_nginx_conf_from_container(nginx_proxy_containers[0])

    def get(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _get(*args, **kwargs):
            return self.session.get(*args, **kwargs)
        return _get(*args, **kwargs)

    def post(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _post(*args, **kwargs):
            return self.session.post(*args, **kwargs)
        return _post(*args, **kwargs)

    def put(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _put(*args, **kwargs):
            return self.session.put(*args, **kwargs)
        return _put(*args, **kwargs)

    def head(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _head(*args, **kwargs):
            return self.session.head(*args, **kwargs)
        return _head(*args, **kwargs)

    def delete(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _delete(*args, **kwargs):
            return self.session.delete(*args, **kwargs)
        return _delete(*args, **kwargs)

    def options(self, *args, **kwargs):
        @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
        def _options(*args, **kwargs):
            return self.session.options(*args, **kwargs)
        return _options(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(requests, name)


def monkey_patch_urllib_dns_resolver():
    """
    Alter the behavior of the urllib DNS resolver so that any domain name
    containing substring 'nginx-proxy' will resolve to the IP address
    of the container created from image 'jwilder/nginx-proxy:test'.
    """
    log = logging.getLogger("patched DNS")
    prv_getaddrinfo = socket.getaddrinfo
    dns_cache = {}
    def new_getaddrinfo(*args):
        log.debug("resolving domain name %s" % repr(args))
        if 'nginx-proxy' in args[0]:
            nginxproxy_container = docker_client.containers.list(filters={"status": "running", "ancestor": "jwilder/nginx-proxy:test"})[0]
            net_info = nginxproxy_container.attrs["NetworkSettings"]["Networks"]
            if "bridge" in net_info:
                ip = net_info["bridge"]["IPAddress"]
            else:
                # not default bridge network, fallback on first network defined
                network_name = net_info.keys()[0]
                ip = net_info[network_name]["IPAddress"]
            log.info("resolving domain name %r as IP address is %s" % (args[0], ip))
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, args[1])), 
                (socket.AF_INET, socket.SOCK_DGRAM, 17, '', (ip, args[1])), 
                (socket.AF_INET, socket.SOCK_RAW, 0, '', (ip, args[1]))
            ]

        try:
            return dns_cache[args]
        except KeyError:
            res = prv_getaddrinfo(*args)
            dns_cache[args] = res
            return res
    socket.getaddrinfo = new_getaddrinfo
    return prv_getaddrinfo

def restore_urllib_dns_resolver(getaddrinfo_func):
    socket.getaddrinfo = getaddrinfo_func


def remove_all_containers():
    for container in docker_client.containers.list(all=True):
        if I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER and container.id.startswith(socket.gethostname()):
            continue  # pytest is running within a Docker container, so we do not want to remove that particular container
        logging.info("removing container %s" % container.name)
        container.remove(v=True, force=True)


def get_nginx_conf_from_container(container):
    """
    return the nginx /etc/nginx/conf.d/default.conf file content from a container
    """
    import tarfile
    from cStringIO import StringIO
    strm, stat = container.get_archive('/etc/nginx/conf.d/default.conf')
    with tarfile.open(fileobj=StringIO(strm.read())) as tf:
        conffile = tf.extractfile('default.conf')
    return conffile.read()


def docker_compose_up(compose_file='docker-compose.yml'):
    logging.info('docker-compose -f %s up -d' % compose_file)
    try:
        subprocess.check_output(shlex.split('docker-compose -f %s up -d' % compose_file))
    except subprocess.CalledProcessError, e:
        logging.error("Error while runninng 'docker-compose -f %s up -d':\n%s" % (compose_file, e.output))
        raise

def docker_compose_down(compose_file='docker-compose.yml'):
    logging.info('docker-compose -f %s down' % compose_file)
    try:
        subprocess.check_output(shlex.split('docker-compose -f %s down' % compose_file))
    except subprocess.CalledProcessError, e:
        logging.error("Error while runninng 'docker-compose -f %s down':\n%s" % (compose_file, e.output))
        raise

def wait_for_nginxproxy_to_be_ready():
    """
    If one (and only one) container started from image jwilder/nginx-proxy:test is found, 
    wait for its log to contain substring "Watching docker events"
    """
    containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        return
    container = containers[0]
    for line in container.logs(stream=True):
        if "Watching docker events" in line:
            time.sleep(1)  # give time to docker-gen to produce the new nginx config and reload nginx
            logging.debug("nginx-proxy ready")
            break

def find_docker_compose_file(request):
    """
    helper for fixture functions to figure out the name of the docker-compose file to consider.

    - if the test module provides a `docker_compose_file` variable, take that
    - else, if a yaml file exists with the same name as the test module (but for the `.yml` extension), use that
    - otherwise use `docker-compose.yml`.
    """
    test_module_dir = os.path.dirname(request.module.__file__)
    yml_file = os.path.join(test_module_dir, request.module.__name__ + '.yml')
    yaml_file = os.path.join(test_module_dir, request.module.__name__ + '.yaml')
    default_file = os.path.join(test_module_dir, 'docker-compose.yml')

    docker_compose_file_module_variable = getattr(request.module, "docker_compose_file", None)
    if docker_compose_file_module_variable is not None:
        docker_compose_file = os.path.join( test_module_dir, docker_compose_file_module_variable)
        if not os.path.isfile(docker_compose_file):
            raise ValueError("docker compose file %r could not be found. Check your test module `docker_compose_file` variable value." % docker_compose_file)
    else:
        if os.path.isfile(yml_file):
            docker_compose_file = yml_file
        elif os.path.isfile(yaml_file):
            docker_compose_file = yaml_file
        else:
            docker_compose_file = default_file

    if not os.path.isfile(docker_compose_file):
        logging.error("Could not find any docker-compose file named either '{0}.yml', '{0}.yaml' or 'docker-compose.yml'".format(request.module.__name__))

    logging.debug("using docker compose file %s" % docker_compose_file)
    return docker_compose_file


def connect_to_network(network):
    """
    If we are running from a container, connect our container to the given network

    :return: the name of the network we were connected to, or None
    """
    if I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER:
        my_container = docker_client.containers.get(socket.gethostname())

        # figure out our container networks
        my_networks = my_container.attrs["NetworkSettings"]["Networks"].keys()

        # make sure our container is connected to the nginx-proxy's network
        if network not in my_networks:
            logging.info("Connecting to docker network: %s" % network.name)
            network.connect(my_container)
            return network


def disconnect_from_network(network=None):
    """
    If we are running from a container, disconnect our container from the given network.

    :param network: name of a docker network to disconnect from
    """
    if I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER and network is not None:
        my_container = docker_client.containers.get(socket.gethostname())

        # figure out our container networks
        my_networks_names = my_container.attrs["NetworkSettings"]["Networks"].keys()

        # disconnect our container from the given network
        if network.name in my_networks_names:
            logging.info("Disconnecting from network %s" % network.name)
            network.disconnect(my_container)


def connect_to_all_networks():
    """
    If we are running from a container, connect our container to all current docker networks.

    :return: a list of networks we connected to
    """
    if not I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER:
        return []
    else:
        # find the list of docker networks
        networks = filter(lambda network: len(network.containers) > 0 and network.name != 'bridge', docker_client.networks.list())
        return [connect_to_network(network) for network in networks]


###############################################################################
# 
# Py.test fixtures
# 
###############################################################################

@pytest.yield_fixture(scope="module")
def docker_compose(request):
    """
    pytest fixture providing containers described in a docker compose file. After the tests, remove the created containers
    
    A custom docker compose file name can be defined in a variable named `docker_compose_file`.
    
    Also, in the case where pytest is running from a docker container, this fixture makes sure
    our container will be attached to all the docker networks.
    """
    docker_compose_file = find_docker_compose_file(request)
    original_dns_resolver = monkey_patch_urllib_dns_resolver()
    remove_all_containers()
    docker_compose_up(docker_compose_file)
    networks = connect_to_all_networks()
    wait_for_nginxproxy_to_be_ready()
    yield
    for network in networks:
        disconnect_from_network(network)
    docker_compose_down(docker_compose_file)
    restore_urllib_dns_resolver(original_dns_resolver)


@pytest.yield_fixture()
def nginxproxy():
    """
    Provides the `nginxproxy` object that can be used in the same way the requests module is:

    r = nginxproxy.get("http://foo.com")

    The difference is that in case an HTTP requests has status code 404 or 502 (which mostly
    indicates that nginx has just reloaded), we retry up to 30 times the query
    """
    yield requests_for_docker()


###############################################################################
# 
# Py.test hooks
# 
###############################################################################

# pytest hook to display additionnal stuff in test report
def pytest_runtest_logreport(report):
    if report.failed:
        test_containers = docker_client.containers.list(all=True, filters={"ancestor": "jwilder/nginx-proxy:test"})
        for container in test_containers:
            report.longrepr.addsection('nginx-proxy logs', container.logs())
            report.longrepr.addsection('nginx-proxy conf', get_nginx_conf_from_container(container))



###############################################################################
# 
# Check requirements
# 
###############################################################################

try:
    docker_client.images.get('jwilder/nginx-proxy:test')
except docker.errors.ImageNotFound:
    pytest.exit("The docker image 'jwilder/nginx-proxy:test' is missing")

if docker.__version__ != "2.0.2":
    pytest.exit("This test suite is meant to work with the python docker module v2.0.2")
