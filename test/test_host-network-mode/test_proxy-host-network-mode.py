# Note: on Docker Desktop, host networking must be manually enabled.
# See https://docs.docker.com/engine/network/drivers/host/
import os

import pytest

PYTEST_RUNNING_IN_CONTAINER = os.environ.get('PYTEST_RUNNING_IN_CONTAINER') == "1"

pytestmark = pytest.mark.skipif(
    PYTEST_RUNNING_IN_CONTAINER,
    reason="Connecting to host network not supported when pytest is running in container"
)

def test_forwards_to_host_network_container_1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://host-network-1.nginx-proxy.tld:8888/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8080\n"


def test_forwards_to_host_network_container_2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://host-network-2.nginx-proxy.tld:8888/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8181\n"
