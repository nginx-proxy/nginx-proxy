import pytest


def test_raw_ipv4_vhost_forwards_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://172.20.0.4")
    assert r.status_code == 200
    web1_container = docker_compose.containers.get("web1")
    assert r.text == f"I'm {web1_container.id[:12]}\n"


def test_raw_ipv6_vhost_forwards_to_web2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://[fd00::4]", ipv6=True)
    assert r.status_code == 200
    web2_container = docker_compose.containers.get("web2")
    assert r.text == f"I'm {web2_container.id[:12]}\n"
