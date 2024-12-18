import docker
import pytest
from packaging.version import Version


raw_version = docker.from_env().version()["Version"]
pytestmark = pytest.mark.skipif(
    Version(raw_version) < Version("1.13"),
    reason="Docker compose syntax v3 requires docker engine v1.13 or later (got {raw_version})"
)


def test_unknown_virtual_host_is_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx.container.docker/")
    assert r.status_code == 503


def test_forwards_to_whoami(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx.container.docker/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == f"I'm {whoami_container.id[:12]}\n"


if __name__ == "__main__":
    import doctest
    doctest.testmod()
