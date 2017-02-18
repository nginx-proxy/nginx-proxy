import os
import docker
import logging
import pytest


def versiontuple(v):
    return tuple(map(int, (v.split("."))))


docker_version = docker.from_env().version()['Version']
pytestmark = pytest.mark.skipif(versiontuple(docker_version) < versiontuple('1.13'),
                                reason="Docker compose syntax v3 requires docker engine v1.13")


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
