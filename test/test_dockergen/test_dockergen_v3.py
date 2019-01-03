import os
import docker
import logging
import pytest
import re

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


@pytest.yield_fixture(scope="module")
def nginx_tmpl():
    """
    pytest fixture which extracts the the nginx config template from
    the jwilder/nginx-proxy:test image
    """
    script_dir = os.path.dirname(__file__)
    logging.info("extracting nginx.tmpl from jwilder/nginx-proxy:test")
    docker_client = docker.from_env()
    print(docker_client.containers.run(
        image='jwilder/nginx-proxy:test',
        remove=True,
        volumes=['{current_dir}:{current_dir}'.format(current_dir=script_dir)],
        entrypoint='sh',
        command='-xc "cp /app/nginx.tmpl {current_dir} && chmod 777 {current_dir}/nginx.tmpl"'.format(
            current_dir=script_dir),
        stderr=True))
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
    assert r.text == "I'm %s\n" % whoami_container.id[:12]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
