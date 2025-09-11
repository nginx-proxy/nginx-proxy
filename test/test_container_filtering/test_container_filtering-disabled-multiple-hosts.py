import pytest


@pytest.mark.flaky
def test_forwards_to_whoami(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx-proxy.tld/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == f"I'm {whoami_container.id[:12]}\n"


@pytest.mark.flaky
def test_forwards_to_whoami2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami2.nginx-proxy.tld/")
    assert r.status_code == 200
    whoami2_container = docker_compose.containers.get("whoami2")
    assert r.text == f"I'm {whoami2_container.id[:12]}\n"
