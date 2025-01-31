import contextlib
import logging
import os
import pathlib
import platform
import re
import shlex
import socket
import subprocess
import time
from io import StringIO
from typing import Iterator, List, Optional

import backoff
import docker.errors
import pytest
import requests
from _pytest.fixtures import FixtureRequest
from docker import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from packaging.version import Version
from requests import Response
from urllib3.util.connection import HAS_IPV6


logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').setLevel(logging.INFO)
logging.getLogger('DNS').setLevel(logging.DEBUG)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

CA_ROOT_CERTIFICATE = pathlib.Path(__file__).parent.joinpath("certs/ca-root.crt")
PYTEST_RUNNING_IN_CONTAINER = os.environ.get('PYTEST_RUNNING_IN_CONTAINER') == "1"
FORCE_CONTAINER_IPV6 = False  # ugly global state to consider containers' IPv6 address instead of IPv4

DOCKER_COMPOSE = os.environ.get('DOCKER_COMPOSE', 'docker compose')

docker_client = docker.from_env()

# Name of pytest container to reference if it's being used for running tests
test_container = 'nginx-proxy-pytest'


###############################################################################
#
# utilities
#
###############################################################################


@contextlib.contextmanager
def ipv6(force_ipv6: bool = True):
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


class RequestsForDocker:
    """
    Proxy for calling methods of the requests module.
    When an HTTP response failed due to HTTP Error 404 or 502, retry a few times.
    Provides method `get_conf` to extract the nginx-proxy configuration content.
    """
    def __init__(self):
        self.session = requests.Session()
        if CA_ROOT_CERTIFICATE.is_file():
            self.session.verify = CA_ROOT_CERTIFICATE.as_posix()

    @staticmethod
    def get_nginx_proxy_container() -> Container:
        """
        Return list of containers
        """
        nginx_proxy_containers = docker_client.containers.list(filters={"ancestor": "nginxproxy/nginx-proxy:test"})
        if len(nginx_proxy_containers) > 1:
            pytest.fail("Too many running nginxproxy/nginx-proxy:test containers", pytrace=False)
        elif len(nginx_proxy_containers) == 0:
            pytest.fail("No running nginxproxy/nginx-proxy:test container", pytrace=False)
        return nginx_proxy_containers.pop()

    def get_conf(self) -> bytes:
        """
        Return the nginx config file
        """
        nginx_proxy_container = self.get_nginx_proxy_container()
        return get_nginx_conf_from_container(nginx_proxy_container)

    def get_ip(self) -> str:
        """
        Return the nginx container ip address
        """
        nginx_proxy_container = self.get_nginx_proxy_container()
        return container_ip(nginx_proxy_container)

    def get(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _get(*_args, **_kwargs):
                return self.session.get(*_args, **_kwargs)
            return _get(*args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _post(*_args, **_kwargs):
                return self.session.post(*_args, **_kwargs)
            return _post(*args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _put(*_args, **_kwargs):
                return self.session.put(*_args, **_kwargs)
            return _put(*args, **kwargs)

    def head(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _head(*_args, **_kwargs):
                return self.session.head(*_args, **_kwargs)
            return _head(*args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _delete(*_args, **_kwargs):
                return self.session.delete(*_args, **_kwargs)
            return _delete(*args, **kwargs)

    def options(self, *args, **kwargs) -> Response:
        with ipv6(kwargs.pop('ipv6', False)):
            @backoff.on_predicate(backoff.constant, lambda r: r.status_code in (404, 502), interval=.3, max_tries=30, jitter=None)
            def _options(*_args, **_kwargs):
                return self.session.options(*_args, **_kwargs)
            return _options(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(requests, name)


def container_ip(container: Container) -> str:
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


def container_ipv6(container: Container) -> str:
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


def nginx_proxy_dns_resolver(domain_name: str) -> Optional[str]:
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
            log.warning(f"no container found from image nginxproxy/nginx-proxy:test while resolving {domain_name!r}")
            exited_nginxproxy_containers = docker_client.containers.list(filters={"status": "exited", "ancestor": "nginxproxy/nginx-proxy:test"})
            if len(exited_nginxproxy_containers) > 0:
                exited_nginxproxy_container_logs = exited_nginxproxy_containers[0].logs()
                log.warning(f"nginxproxy/nginx-proxy:test container might have exited unexpectedly. Container logs: " + "\n" + exited_nginxproxy_container_logs.decode())
            return None
        nginxproxy_container = nginxproxy_containers[0]
        ip = container_ip(nginxproxy_container)
        log.info(f"resolving domain name {domain_name!r} as IP address {ip} of nginx-proxy container {nginxproxy_container.name}")
        return ip

def docker_container_dns_resolver(domain_name: str) -> Optional[str]:
    """
    if domain name is of the form "XXX.container.docker" or "anything.XXX.container.docker",
    return the ip address of the docker container named XXX.

    :return: IP or None
    """
    log = logging.getLogger('DNS')
    log.debug(f"docker_container_dns_resolver({domain_name!r})")

    match = re.search(r'(^|.+\.)(?P<container>[^.]+)\.container\.docker$', domain_name)
    if not match:
        log.debug(f"{domain_name!r} does not match")
        return None

    container_name = match.group('container')
    log.debug(f"looking for container {container_name!r}")
    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound:
        log.warning(f"container named {container_name!r} not found while resolving {domain_name!r}")
        return None
    log.debug(f"container {container.name!r} found ({container.short_id})")

    ip = container_ip(container)
    log.info(f"resolving domain name {domain_name!r} as IP address {ip} of container {container.name}")
    return ip


def monkey_patch_urllib_dns_resolver():
    """
    Alter the behavior of the urllib DNS resolver so that any domain name
    containing substring 'nginx-proxy' will resolve to the IP address
    of the container created from image 'nginxproxy/nginx-proxy:test',
    or to 127.0.0.1 on Darwin.

    see https://docs.docker.com/desktop/features/networking/#i-want-to-connect-to-a-container-from-the-host
    """
    prv_getaddrinfo = socket.getaddrinfo
    dns_cache = {}
    def new_getaddrinfo(*args):
        logging.getLogger('DNS').debug(f"resolving domain name {repr(args)}")
        _args = list(args)

        # Fail early when querying IP directly, and it is forced ipv6 when not supported,
        # Otherwise a pytest container not using the host network fails to pass `test_raw-ip-vhost`.
        if FORCE_CONTAINER_IPV6 and not HAS_IPV6:
            pytest.skip("This system does not support IPv6")

        # custom DNS resolvers
        ip = None
        # Docker Desktop can't route traffic directly to Linux containers.
        if platform.system() == "Darwin":
            ip = "127.0.0.1"
        if ip is None:
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


def get_nginx_conf_from_container(container: Container) -> bytes:
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


def __prepare_and_execute_compose_cmd(compose_files: List[str], project_name: str, cmd: str):
    """
    Prepare and execute the Docker Compose command with the provided compose files and project name.
    """
    compose_cmd = StringIO()
    compose_cmd.write(DOCKER_COMPOSE)
    compose_cmd.write(f" --project-name {project_name}")
    for compose_file in compose_files:
        compose_cmd.write(f" --file {compose_file}")
    compose_cmd.write(f" {cmd}")

    logging.info(compose_cmd.getvalue())
    try:
        subprocess.check_output(shlex.split(compose_cmd.getvalue()), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Error while running '{compose_cmd.getvalue()}':\n{e.output}", pytrace=False)


def docker_compose_up(compose_files: List[str], project_name: str):
    """
    Execute compose up --detach with the provided compose files and project name.
    """
    if compose_files is None or len(compose_files) == 0:
        pytest.fail(f"No compose file passed to docker_compose_up", pytrace=False)
    __prepare_and_execute_compose_cmd(compose_files, project_name, cmd="up --detach")


def docker_compose_down(compose_files: List[str], project_name: str):
    """
    Execute compose down --volumes with the provided compose files and project name.
    """
    if compose_files is None or len(compose_files) == 0:
        pytest.fail(f"No compose file passed to docker_compose_up", pytrace=False)
    __prepare_and_execute_compose_cmd(compose_files, project_name, cmd="down --volumes")


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
def docker_compose_files(request: FixtureRequest) -> List[str]:
    """Fixture returning the docker compose files to consider:

    If a YAML file exists with the same name as the test module (with the `.py` extension
    replaced with `.base.yml`, ie `test_foo.py`-> `test_foo.base.yml`) and in the same
    directory as the test module, use only that file.

    Otherwise, merge the following files in this order:

    - the `compose.base.yml` file in the parent `test` directory.
    - if present in the same directory as the test module, the `compose.base.override.yml` file.
    - the YAML file named after the current test module (ie `test_foo.py`-> `test_foo.yml`)

    Tests can override this fixture to specify a custom location.
    """
    compose_files: List[str] = []
    test_module_path = pathlib.Path(request.module.__file__).parent

    module_base_file = test_module_path.joinpath(f"{request.module.__name__}.base.yml")
    if module_base_file.is_file():
        return [module_base_file.as_posix()]

    global_base_file = test_module_path.parent.joinpath("compose.base.yml")
    if global_base_file.is_file():
        compose_files.append(global_base_file.as_posix())

    module_base_override_file = test_module_path.joinpath("compose.base.override.yml")
    if module_base_override_file.is_file():
        compose_files.append(module_base_override_file.as_posix())

    module_compose_file = test_module_path.joinpath(f"{request.module.__name__}.yml")
    if module_compose_file.is_file():
        compose_files.append(module_compose_file.as_posix())

    if not module_base_file.is_file() and not module_compose_file.is_file():
        logging.error(
            f"Could not find any docker compose file named '{module_base_file.name}' or '{module_compose_file.name}'"
        )

    logging.debug(f"using docker compose files {compose_files}")
    return compose_files


def connect_to_network(network: Network) -> Optional[Network]:
    """
    If we are running from a container, connect our container to the given network

    :return: the name of the network we were connected to, or None
    """
    if PYTEST_RUNNING_IN_CONTAINER:
        try:
            my_container = docker_client.containers.get(test_container)
        except docker.errors.NotFound:
            logging.warning(f"container {test_container} not found")
            return None

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


def disconnect_from_network(network: Network = None):
    """
    If we are running from a container, disconnect our container from the given network.

    :param network: name of a docker network to disconnect from
    """
    if PYTEST_RUNNING_IN_CONTAINER and network is not None:
        try:
            my_container = docker_client.containers.get(test_container)
        except docker.errors.NotFound:
            logging.warning(f"container {test_container} not found")
            return

        # figure out our container networks
        my_networks_names = list(my_container.attrs["NetworkSettings"]["Networks"].keys())

        # disconnect our container from the given network
        if network.name in my_networks_names:
            logging.info(f"Disconnecting from network {network.name}")
            network.disconnect(my_container)


def connect_to_all_networks() -> List[Network]:
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
        self._networks = None
        self._docker_compose_files = None
        self._project_name = None

    def __exit__(self, *exc_info):
        self._down()

    def _down(self):
        if self._docker_compose_files is None:
            return
        for network in self._networks:
            disconnect_from_network(network)
        docker_compose_down(self._docker_compose_files, self._project_name)
        self._docker_compose_file = None
        self._project_name = None

    def compose(self, docker_compose_files: List[str], project_name: str):
        if docker_compose_files == self._docker_compose_files and project_name == self._project_name:
            return
        self._down()
        if docker_compose_files is None or project_name is None:
            return
        docker_compose_up(docker_compose_files, project_name)
        self._networks = connect_to_all_networks()
        wait_for_nginxproxy_to_be_ready()
        time.sleep(3)  # give time to containers to be ready
        self._docker_compose_files = docker_compose_files
        self._project_name = project_name


###############################################################################
#
# Py.test fixtures
#
###############################################################################


@pytest.fixture(scope="module")
def docker_composer() -> Iterator[DockerComposer]:
    with DockerComposer() as d:
        yield d


@pytest.fixture
def ca_root_certificate() -> str:
    return CA_ROOT_CERTIFICATE.as_posix()


@pytest.fixture
def monkey_patched_dns():
    original_dns_resolver = monkey_patch_urllib_dns_resolver()
    yield
    restore_urllib_dns_resolver(original_dns_resolver)


@pytest.fixture
def docker_compose(
        request: FixtureRequest,
        monkeypatch,
        monkey_patched_dns,
        docker_composer,
        docker_compose_files
) -> Iterator[DockerClient]:
    """
    Ensures containers necessary for the test module are started in a compose project,
    and set the environment variable `PYTEST_MODULE_PATH` to the test module's parent folder.

    A list of custom docker compose files path can be specified by overriding
    the `docker_compose_file` fixture.

    Also, in the case where pytest is running from a docker container, this fixture
    makes sure our container will be attached to all the docker networks.
    """
    pytest_module_path = pathlib.Path(request.module.__file__).parent
    monkeypatch.setenv("PYTEST_MODULE_PATH", pytest_module_path.as_posix())

    project_name = request.module.__name__
    docker_composer.compose(docker_compose_files, project_name)

    yield docker_client


@pytest.fixture
def nginxproxy() -> Iterator[RequestsForDocker]:
    """
    Provides the `nginxproxy` object that can be used in the same way the requests module is:

    r = nginxproxy.get("https://foo.com")

    The difference is that in case an HTTP requests has status code 404 or 502 (which mostly
    indicates that nginx has just reloaded), we retry up to 30 times the query.

    Also, the nginxproxy methods accept an additional keyword parameter: `ipv6` which forces requests
    made against containers to use the containers IPv6 address when set to `True`. If IPv6 is not
    supported by the system or docker, that particular test will be skipped.
    """
    yield RequestsForDocker()


@pytest.fixture
def acme_challenge_path() -> str:
    """
    Provides fake Let's Encrypt ACME challenge path used in certain tests
    """
    return ".well-known/acme-challenge/test-filename"

###############################################################################
#
# Py.test hooks
#
###############################################################################

# pytest hook to display additional stuff in test report
def pytest_runtest_logreport(report):
    if report.failed:
        test_containers = docker_client.containers.list(all=True, filters={"ancestor": "nginxproxy/nginx-proxy:test"})
        for container in test_containers:
            report.longrepr.addsection('nginx-proxy logs', container.logs().decode())
            report.longrepr.addsection('nginx-proxy conf', get_nginx_conf_from_container(container).decode())


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

if Version(docker.__version__) < Version("5.0.0"):
    pytest.exit("This test suite is meant to work with the python docker module v5.0.0 or later")
