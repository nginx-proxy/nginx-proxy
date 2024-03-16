from time import sleep

import pytest
from docker.errors import NotFound

@pytest.mark.parametrize("stub,expected_port", [
    ("nginx-proxy.test/web1", 81),
    ("nginx-proxy.test/web2", 82),
    ("nginx-proxy.test", 83),
    ("foo.nginx-proxy.test", 42),
])
def test_valid_path(docker_compose, nginxproxy, stub, expected_port):
    r = nginxproxy.get(f"http://{stub}/port")
    assert r.status_code == 200
    assert r.text == f"answer from port {expected_port}\n"

@pytest.mark.parametrize("stub", [
    "nginx-proxy.test/foo",
    "bar.nginx-proxy.test",
])
def test_invalid_path(docker_compose, nginxproxy, stub):
    r = nginxproxy.get(f"http://{stub}/port")
    assert r.status_code in [404, 503]

@pytest.fixture()
def web4(docker_compose):
    """
    pytest fixture creating a web container with `VIRTUAL_HOST=nginx-proxy.test`, `VIRTUAL_PATH=/web4/` and `VIRTUAL_DEST=/` listening on port 84.
    """
    container = docker_compose.containers.run(
        name="web4",
        image="web",
        detach=True,
        environment={
            "WEB_PORTS": "84",
            "VIRTUAL_HOST": "nginx-proxy.test",
            "VIRTUAL_PATH": "/web4/",
            "VIRTUAL_DEST": "/",
        },
        ports={"84/tcp": None}
    )
    docker_compose.networks.get("test_virtual-path_default").connect(container)
    sleep(2)  # give it some time to initialize and for docker-gen to detect it
    yield container
    try:
        docker_compose.containers.get("web4").remove(force=True)
    except NotFound:
        pass

"""
Test if we can add and remove a single virtual_path from multiple ones on the same subdomain.
"""
def test_container_hotplug(web4, nginxproxy):
    r = nginxproxy.get(f"http://nginx-proxy.test/web4/port")
    assert r.status_code == 200
    assert r.text == f"answer from port 84\n"
    web4.remove(force=True)
    sleep(2)
    r = nginxproxy.get(f"http://nginx-proxy.test/web4/port")
    assert r.status_code == 404
