"""
Test that nginx-proxy detects new containers
"""
from time import sleep

import pytest
from docker.errors import NotFound


@pytest.fixture()
def web1(docker_compose):
    """
    pytest fixture creating a web container with `VIRTUAL_HOST=web1.nginx-proxy` listening on port 81.
    """
    container = docker_compose.containers.run(
        name="web1",
        image="web",
        detach=True,
        environment={
            "WEB_PORTS": "81",
            "VIRTUAL_HOST": "web1.nginx-proxy"
        },
        ports={"81/tcp": None}
    )
    docker_compose.networks.get("test_default").connect(container)
    sleep(2)  # give it some time to initialize and for docker-gen to detect it
    yield container
    try:
        docker_compose.containers.get("web1").remove(force=True)
    except NotFound:
        pass

@pytest.fixture()
def web2(docker_compose):
    """
    pytest fixture creating a web container with `VIRTUAL_HOST=nginx-proxy`, `VIRTUAL_PATH=/web2/` and `VIRTUAL_DEST=/` listening on port 82.
    """
    container = docker_compose.containers.run(
        name="web2",
        image="web",
        detach=True,
        environment={
            "WEB_PORTS": "82",
            "VIRTUAL_HOST": "nginx-proxy",
            "VIRTUAL_PATH": "/web2/",
            "VIRTUAL_DEST": "/",
        },
        ports={"82/tcp": None}
    )
    docker_compose.networks.get("test_default").connect(container)
    sleep(2)  # give it some time to initialize and for docker-gen to detect it
    yield container
    try:
        docker_compose.containers.get("web2").remove(force=True)
    except NotFound:
        pass

def test_nginx_proxy_behavior_when_alone(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503


def test_new_container_is_detected_vhost(web1, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy/port")
    assert r.status_code == 200
    assert "answer from port 81\n" == r.text

    web1.remove(force=True)
    sleep(2)
    r = nginxproxy.get("http://web1.nginx-proxy/port")
    assert r.status_code == 503

def test_new_container_is_detected_vpath(web2, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/web2/port")
    assert r.status_code == 200
    assert "answer from port 82\n" == r.text
    r = nginxproxy.get("http://nginx-proxy/port")
    assert r.status_code in [404, 503]

    web2.remove(force=True)
    sleep(2)
    r = nginxproxy.get("http://nginx-proxy/web2/port")
    assert r.status_code == 503

