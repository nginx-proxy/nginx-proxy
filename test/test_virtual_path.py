import pytest


def test_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"

def test_simple_path(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/foo/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n"

def test_deep_path(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/bar/even/deeper/port")
    assert r.status_code == 200
    assert r.text == "answer from port 83\n"

def test_closed_path(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/bar/even/deeper/with/end/port")
    assert r.status_code == 200
    assert r.text == "answer from port 84\n"

