import contextlib
import logging
import os
import re
import shlex
import socket
import subprocess
import time
from typing import List

import backoff
import docker
import pytest
import requests
from _pytest._code.code import ReprExceptionInfo
from distutils.version import LooseVersion
from docker.models.containers import Container
from requests.packages.urllib3.util.connection import HAS_IPV6

logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').setLevel(logging.INFO)
logging.getLogger('DNS').setLevel(logging.DEBUG)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

CA_ROOT_CERTIFICATE = os.path.join(os.path.dirname(__file__), 'certs/ca-root.crt')
PYTEST_RUNNING_IN_CONTAINER = os.environ.get('PYTEST_RUNNING_IN_CONTAINER') == "1"
FORCE_CONTAINER_IPV6 = False  # ugly global state to consider containers' IPv6 address instead of IPv4


docker_client = docker.from_env()

# Name of pytest container to reference if it's being used for running tests
test_container = 'nginx-proxy-pytest'


###############################################################################
#
# utilities
#
###############################################################################

@contextlib.contextmanager
def ipv6(force_ipv6=True):
    """
    Meant to be used as a context manager to force IPv6 sockets:

        with ipv6():
            nginxproxy.get("http://something.nginx-proxy.example")  # force use of IPv6

        with ipv6(False):
            nginxproxy.get("http://something.nginx-proxy.example")  # legacy behavior


    """
    global FORCE_CONTAINER_IPV6
    FORCE_CONTAINER_IPV6 = force_ipv6
    yield
    FORCE_CONTAINER_IPV6 = False


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

    @staticmethod
    def get_nginx_proxy_containers() -> List[Container]:
        """
        Return list of containers
        """
        nginx_proxy_containers = docker_client.containers.list(filters={"ancestor": "nginxproxy/nginx-proxy:test"})
        if len(nginx_proxy_containers) > 1:
            pytest.fail("Too many running nginxproxy/nginx-proxy:test containers", pytrace=False)
        elif len(nginx_proxy_containers) == 0:
            pytest.fail("No running nginxproxy/nginx-proxy:test container", pytrace=False)
        return nginx_proxy_containers

    def get_conf(self):
        """
        Return the nginx config file
        """
        nginx_proxy_containers = self.get_nginx_proxy_containers()
        return get_nginx_conf_from_container(nginx_proxy_containers[0])

    def get_ip(self) -> str:
        """
        Return the nginx container ip address
        """
        nginx_proxy_containers = self.get_nginx_proxy_containers()
        return container_ip(nginx_proxy_containers[0])

    def get(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _get(*args, **kwargs):
                return self.session.get(*args, **kwargs)
            return _get(*args, **kwargs)

    def post(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _post(*args, **kwargs):
                return self.session.post(*args, **kwargs)
            return _post(*args, **kwargs)

    def put(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _put(*args, **kwargs):
                return self.session.put(*args, **kwargs)
            return _put(*args, **kwargs)

    def head(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _head(*args, **kwargs):
                return self.session.head(*args, **kwargs)
            return _head(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _delete(*args, **kwargs):
                return self.session.delete(*args, **kwargs)
            return _delete(*args, **kwargs)

    def options(self, *args, **kwargs):
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _options(*args, **kwargs):
                return self.session.options(*args, **kwargs)
            return _options(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(requests, name)


def container_ip(container: Container):
    """
    return the IP address of a container.

    If the global FORCE_CONTAINER_IPV6 flag is set, return the IPv6 address
    """
    global FORCE_CONTAINER_IPV6
    if FORCE_CONTAINER_IPV6:
        if not HAS_IPV6:
            pytest.skip("This system does not support IPv6")
        ip = container_ipv6(container)
        if ip == '':
            pytest.skip(f"Container {container.name} has no IPv6 address")
        else:
            return ip
    else:
        net_info = container.attrs["NetworkSettings"]["Networks"]
        if "bridge" in net_info:
            return net_info["bridge"]["IPAddress"]
        
        # container is running in host network mode
        if "host" in net_info:
            return "127.0.0.1"

        # not default bridge network, fallback on first network defined
        network_name = list(net_info.keys())[0]
        return net_info[network_name]["IPAddress"]


def container_ipv6(container):
    """
    return the IPv6 address of a container.
    """
    net_info = container.attrs["NetworkSettings"]["Networks"]
    if "bridge" in net_info:
        return net_info["bridge"]["GlobalIPv6Address"]
    
    # container is running in host network mode
    if "host" in net_info:
        return "::1"

    # not default bridge network, fallback on first network defined
    network_name = list(net_info.keys())[0]
    return net_info[network_name]["GlobalIPv6Address"]


def nginx_proxy_dns_resolver(domain_name):
    """
    if "nginx-proxy" if found in host, return the ip address of the docker container
    issued from the docker image nginxproxy/nginx-proxy:test.

    :return: IP or None
    """
    log = logging.getLogger('DNS')
    log.debug(f"nginx_proxy_dns_resolver({domain_name!r})")
    if 'nginx-proxy' in domain_name:
        nginxproxy_containers = docker_client.containers.list(filters={"status": "running", "ancestor": "nginxproxy/nginx-proxy:test"})
        if len(nginxproxy_containers) == 0:
            log.warn(f"no container found from image nginxproxy/nginx-proxy:test while resolving {domain_name!r}")
            exited_nginxproxy_containers = docker_client.containers.list(filters={"status": "exited", "ancestor": "nginxproxy/nginx-proxy:test"})
            if len(exited_nginxproxy_containers) > 0:
                exited_nginxproxy_container_logs = exited_nginxproxy_containers[0].logs()
                log.warn(f"nginxproxy/nginx-proxy:test container might have exited unexpectedly. Container logs: " + "\n" + exited_nginxproxy_container_logs.decode())
            return
        nginxproxy_container = nginxproxy_containers[0]
        ip = container_ip(nginxproxy_container)
        log.info(f"resolving domain name {domain_name!r} as IP address {ip} of nginx-proxy container {nginxproxy_container.name}")
        return ip

def docker_container_dns_resolver(domain_name):
    """
    if domain name is of the form "XXX.container.docker" or "anything.XXX.container.docker", return the ip address of the docker container
    named XXX.

    :return: IP or None
    """
    log = logging.getLogger('DNS')
    log.debug(f"docker_container_dns_resolver({domain_name!r})")

    match = re.search(r'(^|.+\.)(?P<container>[^.]+)\.container\.docker$', domain_name)
    if not match:
        log.debug(f"{domain_name!r} does not match")
        return

    container_name = match.group('container')
    log.debug(f"looking for container {container_name!r}")
    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound:
        log.warn(f"container named {container_name!r} not found while resolving {domain_name!r}")
        return
    log.debug(f"container {container.name!r} found ({container.short_id})")

    ip = container_ip(container)
    log.info(f"resolving domain name {domain_name!r} as IP address {ip} of container {container.name}")
    return ip


def monkey_patch_urllib_dns_resolver():
    """
    Alter the behavior of the urllib DNS resolver so that any domain name
    containing substring 'nginx-proxy' will resolve to the IP address
    of the container created from image 'nginxproxy/nginx-proxy:test'.
    """
    prv_getaddrinfo = socket.getaddrinfo
    dns_cache = {}
    def new_getaddrinfo(*args):
        logging.getLogger('DNS').debug(f"resolving domain name {repr(args)}")
        _args = list(args)

        # Fail early when querying IP directly and it is forced ipv6 when not supported,
        # Otherwise a pytest container not using the host network fails to pass `test_raw-ip-vhost`.
        if FORCE_CONTAINER_IPV6 and not HAS_IPV6:
            pytest.skip("This system does not support IPv6")

        # custom DNS resolvers
        ip = nginx_proxy_dns_resolver(args[0])
        if ip is None:
            ip = docker_container_dns_resolver(args[0])
        if ip is not None:
            _args[0] = ip

        # call on original DNS resolver, with eventually the original host changed to the wanted IP address
        try:
            return dns_cache[tuple(_args)]
        except KeyError:
            res = prv_getaddrinfo(*_args)
            dns_cache[tuple(_args)] = res
            return res
    socket.getaddrinfo = new_getaddrinfo
    return prv_getaddrinfo

def restore_urllib_dns_resolver(getaddrinfo_func):
    socket.getaddrinfo = getaddrinfo_func


def remove_all_containers():
    for container in docker_client.containers.list(all=True):
        if PYTEST_RUNNING_IN_CONTAINER and container.name == test_container:
            continue  # pytest is running within a Docker container, so we do not want to remove that particular container
        logging.info(f"removing container {container.name}")
        container.remove(v=True, force=True)


def get_nginx_conf_from_container(container):
    """
    return the nginx /etc/nginx/conf.d/default.conf file content from a container
    """
    import tarfile
    from io import BytesIO

    strm_generator, stat = container.get_archive('/etc/nginx/conf.d/default.conf')
    strm_fileobj = BytesIO(b"".join(strm_generator))

    with tarfile.open(fileobj=strm_fileobj) as tf:
        conffile = tf.extractfile('default.conf')
        return conffile.read()


def docker_compose_up(compose_file='docker-compose.yml'):
    logging.info(f'docker-compose -f {compose_file} up -d')
    try:
        subprocess.check_output(shlex.split(f'docker-compose -f {compose_file} up -d'), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Error while runninng 'docker-compose -f {compose_file} up -d':\n{e.output}", pytrace=False)


def docker_compose_down(compose_file='docker-compose.yml'):
    logging.info(f'docker-compose -f {compose_file} down -v')
    try:
        subprocess.check_output(shlex.split(f'docker-compose -f {compose_file} down -v'), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Error while runninng 'docker-compose -f {compose_file} down -v':\n{e.output}", pytrace=False)


def wait_for_nginxproxy_to_be_ready():
    """
    If one (and only one) container started from image nginxproxy/nginx-proxy:test is found,
    wait for its log to contain substring "Watching docker events"
    """
    containers = docker_client.containers.list(filters={"ancestor": "nginxproxy/nginx-proxy:test"})
    if len(containers) != 1:
        return
    container = containers[0]
    for line in container.logs(stream=True):
        if b"Watching docker events" in line:
            logging.debug("nginx-proxy ready")
            break


@pytest.fixture
def docker_compose_file(request):
    """Fixture naming the docker-compose file to consider.

    If a YAML file exists with the same name as the test module (with the `.py` extension replaced
    with `.yml` or `.yaml`), use that.  Otherwise, use `docker-compose.yml` in the same directory
    as the test module.

    Tests can override this fixture to specify a custom location.
    """
    test_module_dir = os.path.dirname(request.module.__file__)
    yml_file = os.path.join(test_module_dir, request.module.__name__ + '.yml')
    yaml_file = os.path.join(test_module_dir, request.module.__name__ + '.yaml')
    default_file = os.path.join(test_module_dir, 'docker-compose.yml')

    if os.path.isfile(yml_file):
        docker_compose_file = yml_file
    elif os.path.isfile(yaml_file):
        docker_compose_file = yaml_file
    else:
        docker_compose_file = default_file

    if not os.path.isfile(docker_compose_file):
        logging.error("Could not find any docker-compose file named either '{0}.yml', '{0}.yaml' or 'docker-compose.yml'".format(request.module.__name__))

    logging.debug(f"using docker compose file {docker_compose_file}")
    return docker_compose_file


def connect_to_network(network):
    """
    If we are running from a container, connect our container to the given network

    :return: the name of the network we were connected to, or None
    """
    if PYTEST_RUNNING_IN_CONTAINER:
        try:
            my_container = docker_client.containers.get(test_container)
        except docker.errors.NotFound:
            logging.warn(f"container {test_container} not found")
            return

        # figure out our container networks
        my_networks = list(my_container.attrs["NetworkSettings"]["Networks"].keys())

        # If the pytest container is using host networking, it cannot connect to container networks (not required with host network) 
        if 'host' in my_networks:
            return None

        # Make sure our container is connected to the nginx-proxy's network,
        # but avoid connecting to `none` network (not valid) with `test_server-down` tests
        if network.name not in my_networks and network.name != 'none':
            logging.info(f"Connecting to docker network: {network.name}")
            network.connect(my_container)
            return network


def disconnect_from_network(network=None):
    """
    If we are running from a container, disconnect our container from the given network.

    :param network: name of a docker network to disconnect from
    """
    if PYTEST_RUNNING_IN_CONTAINER and network is not None:
        try:
            my_container = docker_client.containers.get(test_container)
        except docker.errors.NotFound:
            logging.warn(f"container {test_container} not found")
            return

        # figure out our container networks
        my_networks_names = list(my_container.attrs["NetworkSettings"]["Networks"].keys())

        # disconnect our container from the given network
        if network.name in my_networks_names:
            logging.info(f"Disconnecting from network {network.name}")
            network.disconnect(my_container)


def connect_to_all_networks():
    """
    If we are running from a container, connect our container to all current docker networks.

    :return: a list of networks we connected to
    """
    if not PYTEST_RUNNING_IN_CONTAINER:
        return []
    else:
        # find the list of docker networks
        networks = [network for network in docker_client.networks.list(greedy=True) if len(network.containers) > 0 and network.name != 'bridge']
        return [connect_to_network(network) for network in networks]


class DockerComposer(contextlib.AbstractContextManager):
    def __init__(self):
        self._docker_compose_file = None

    def __exit__(self, *exc_info):
        self._down()

    def _down(self):
        if self._docker_compose_file is None:
            return
        for network in self._networks:
            disconnect_from_network(network)
        docker_compose_down(self._docker_compose_file)
        self._docker_compose_file = None

    def compose(self, docker_compose_file):
        if docker_compose_file == self._docker_compose_file:
            return
        self._down()
        if docker_compose_file is None:
            return
        remove_all_containers()
        docker_compose_up(docker_compose_file)
        self._networks = connect_to_all_networks()
        wait_for_nginxproxy_to_be_ready()
        time.sleep(3)  # give time to containers to be ready
        self._docker_compose_file = docker_compose_file


###############################################################################
#
# Py.test fixtures
#
###############################################################################


@pytest.fixture(scope="module")
def docker_composer():
    with DockerComposer() as d:
        yield d


@pytest.fixture
def ca_root_certificate():
    return CA_ROOT_CERTIFICATE


@pytest.fixture
def monkey_patched_dns():
    original_dns_resolver = monkey_patch_urllib_dns_resolver()
    yield
    restore_urllib_dns_resolver(original_dns_resolver)


@pytest.fixture
def docker_compose(monkey_patched_dns, docker_composer, docker_compose_file):
    """Ensures containers described in a docker compose file are started.

    A custom docker compose file name can be specified by overriding the `docker_compose_file`
    fixture.

    Also, in the case where pytest is running from a docker container, this fixture makes sure
    our container will be attached to all the docker networks.
    """
    docker_composer.compose(docker_compose_file)
    yield docker_client


@pytest.fixture()
def nginxproxy():
    """
    Provides the `nginxproxy` object that can be used in the same way the requests module is:

    r = nginxproxy.get("http://foo.com")

    The difference is that in case an HTTP requests has status code 404 or 502 (which mostly
    indicates that nginx has just reloaded), we retry up to 30 times the query.

    Also, the nginxproxy methods accept an additional keyword parameter: `ipv6` which forces requests
    made against containers to use the containers IPv6 address when set to `True`. If IPv6 is not
    supported by the system or docker, that particular test will be skipped.
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
        if isinstance(report.longrepr, ReprExceptionInfo):
            test_containers = docker_client.containers.list(all=True, filters={"ancestor": "nginxproxy/nginx-proxy:test"})
            for container in test_containers:
                report.longrepr.addsection('nginx-proxy logs', container.logs())
                report.longrepr.addsection('nginx-proxy conf', get_nginx_conf_from_container(container))


# Py.test `incremental` marker, see http://stackoverflow.com/a/12579625/107049
def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    previousfailed = getattr(item.parent, "_previousfailed", None)
    if previousfailed is not None:
        pytest.xfail(f"previous test failed ({previousfailed.name})")

###############################################################################
#
# Check requirements
#
###############################################################################

try:
    docker_client.images.get('nginxproxy/nginx-proxy:test')
except docker.errors.ImageNotFound:
    pytest.exit("The docker image 'nginxproxy/nginx-proxy:test' is missing")

if LooseVersion(docker.__version__) < LooseVersion("5.0.0"):
    pytest.exit("This test suite is meant to work with the python docker module v5.0.0 or later")
