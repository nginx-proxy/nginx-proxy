import pytest


def test_fallback_on_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"