import pytest


def test_unknown_virtual_host_is_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx-proxy.tld/port")
    assert r.status_code == 503

def test_webA_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://webA.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 5000\n"

def test_webB_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://webB.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 5001\n"
