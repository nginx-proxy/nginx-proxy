import os
import docker
import logging
import pytest
import re
from distutils.version import LooseVersion


raw_version = docker.from_env().version()["Version"]
pytestmark = pytest.mark.skipif(
    LooseVersion(raw_version) < LooseVersion("1.13"),
    reason="Docker compose syntax v3 requires docker engine v1.13 or later (got {raw_version})"
)


@pytest.fixture(scope="module")
def nginx_tmpl():
    """
    pytest fixture which extracts the the nginx config template from
    the nginxproxy/nginx-proxy:test image
    """
    script_dir = os.path.dirname(__file__)
    logging.info("extracting nginx.tmpl from nginxproxy/nginx-proxy:test")
    docker_client = docker.from_env()
    print(
        docker_client.containers.run(
            image="nginxproxy/nginx-proxy:test",
            remove=True,
            volumes=["{current_dir}:{current_dir}".format(current_dir=script_dir)],
            entrypoint="sh",
            command='-xc "cp /app/nginx.tmpl {current_dir} && chmod 777 {current_dir}/nginx.tmpl"'.format(
                current_dir=script_dir
            ),
            stderr=True,
        )
    )
    yield
    logging.info("removing nginx.tmpl")
    os.remove(os.path.join(script_dir, "nginx.tmpl"))


def test_unknown_virtual_host_is_503(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx.container.docker/")
    assert r.status_code == 503


def test_forwards_to_whoami(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx.container.docker/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == f"I'm {whoami_container.id[:12]}\n"


if __name__ == "__main__":
    import doctest
    doctest.testmod()
