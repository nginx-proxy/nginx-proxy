import pytest


@pytest.mark.flaky
def test_whoami2_is_503(docker_compose, nginxproxy):
    whoami2_container = docker_compose.containers.get("whoami2")
    assert whoami2_container.status == "running"
    r = nginxproxy.get("http://whoami2.nginx-proxy.tld/")
    assert r.status_code == 503


@pytest.mark.flaky
def test_forwards_to_whoami(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx-proxy.tld/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == f"I'm {whoami_container.id[:12]}\n"
