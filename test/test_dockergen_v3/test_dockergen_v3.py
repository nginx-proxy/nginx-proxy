from time import sleep
import docker
import pytest


def versiontuple(v):
    """
    >>> versiontuple("1.12.3")
    (1, 12, 3)

    >>> versiontuple("1.13.0")
    (1, 13, 0)

    >>> versiontuple("17.03.0-ce")
    (17, 3, 0)

    >>> versiontuple("17.03.0-ce") < (1, 13)
    False
    """
    return tuple(map(int, (v.split('-')[0].split("."))))


raw_version = docker.from_env().version()['Version']
pytestmark = pytest.mark.skipif(
    versiontuple(raw_version) < (1, 13),
    reason="Docker compose syntax v3 requires docker engine v1.13 or later (got %s)" % raw_version)


def test_nginx_is_running(nginx_tmpl, docker_compose):
    sleep(3)
    assert docker_compose.containers.get("nginx").status == "running"


def test_unknown_virtual_host_is_503(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx.container.docker/")
    assert r.status_code == 503


def test_forwards_to_whoami(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx.container.docker/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == "I'm %s\n" % whoami_container.id[:12]
