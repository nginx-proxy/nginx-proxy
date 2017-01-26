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

logging.basicConfig(level=logging.WARNING)
logging.getLogger('backoff').setLevel(logging.INFO)
logging.getLogger('patched DNS').setLevel(logging.INFO)


CA_ROOT_CERTIFICATE = os.path.join(os.path.dirname(__file__), 'certs/ca-root.crt')
I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER = os.path.isfile("/.dockerenv")

###############################################################################
# 
# utilities
# 
###############################################################################


class requests_retry_on_error_502(object):
    """
    Proxy for calling methods of the requests module. 
    When a HTTP response failed due to HTTP Error 404 or 502, retry up to 30 times.
    """
    def __init__(self):
        self.session = requests.Session()
        if os.path.isfile(CA_ROOT_CERTIFICATE):
            self.session.verify = CA_ROOT_CERTIFICATE

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
            docker_client = docker.from_env()
            net_info = docker_client.containers(filters={"status": "running", "ancestor": "jwilder/nginx-proxy:test"})[0]["NetworkSettings"]["Networks"]
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
    docker_client = docker.from_env()
    for info in docker_client.containers(all=True):
        if I_AM_RUNNING_INSIDE_A_DOCKER_CONTAINER and info['Id'].startswith(socket.gethostname()):
            continue  # pytest is running within a Docker container, so we do not want to remove that particular container
        docker_client.remove_container(info["Id"], v=True, force=True)


def get_nginx_conf_from_container(container_id):
    """
    return the nginx /etc/nginx/conf.d/default.conf file content from a container
    """
    import tarfile
    from cStringIO import StringIO
    docker_client = docker.from_env()
    strm, stat = docker_client.get_archive(container_id, '/etc/nginx/conf.d/default.conf')
    with tarfile.open(fileobj=StringIO(strm.read())) as tf:
        conffile = tf.extractfile('default.conf')
    return conffile.read()


def docker_compose_up(compose_file='docker-compose.yml'):
    try:
        subprocess.check_output(shlex.split('docker-compose -f %s up -d' % compose_file))
    except subprocess.CalledProcessError, e:
        logging.error("Error while runninng 'docker-compose -f %s up -d':\n%s" % (compose_file, e.output))
        raise

def wait_for_nginxproxy_to_be_ready():
    """
    If a one (and only one) container started from image jwilder/nginx-proxy:test is found, 
    wait for its log to contain substring "Watching docker events"
    """
    docker_client = docker.from_env()
    containers = docker_client.containers(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        return
    container = containers[0]
    for line in docker_client.logs(container['Id'], stream=True):
        if "Watching docker events" in line:
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

    logging.info("using docker compose file %s" % docker_compose_file)
    return docker_compose_file


def check_sut_image():
    """
    Return True if jwilder/nginx-proxy:test image exists
    """
    docker_client = docker.from_env()
    return any(map(lambda x: "jwilder/nginx-proxy:test" in x.get('RepoTags'), docker_client.images()))

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
    """
    docker_compose_file = find_docker_compose_file(request)
    original_dns_resolver = monkey_patch_urllib_dns_resolver()
    if not check_sut_image():
        pytest.exit("The docker image 'jwilder/nginx-proxy:test' is missing")
    remove_all_containers()
    docker_compose_up(docker_compose_file)
    wait_for_nginxproxy_to_be_ready()
    time.sleep(3)
    yield
    restore_urllib_dns_resolver(original_dns_resolver)


@pytest.fixture(scope="session")
def nginxproxy():
    """
    Provides the `nginxproxy` object that can be used in the same way the requests module is:

    r = nginxproxy.get("http://foo.com")

    The difference is that in case an HTTP requests has status code 404 or 502 (which mostly
    indicates that nginx has just reloaded), we retry up to 30 times the query
    """
    return requests_retry_on_error_502() 


###############################################################################
# 
# Py.test hooks
# 
###############################################################################

# pytest hook to display additionnal stuff in test report
def pytest_runtest_logreport(report):
    if report.failed:
        docker_client = docker.from_env()
        test_containers = docker_client.containers(all=True, filters={"ancestor": "jwilder/nginx-proxy:test"})
        for container in test_containers:
            report.longrepr.addsection('nginx-proxy logs', docker_client.logs(container['Id']))
            report.longrepr.addsection('nginx-proxy conf', get_nginx_conf_from_container(container['Id']))

