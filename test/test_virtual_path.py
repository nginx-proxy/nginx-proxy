import pytest


def test_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"

def test_simple_path_not_stripped(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/foo/port")
    assert r.status_code == 404

def test_simple_path_stripped(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/bar/port")
    assert r.status_code == 200
    assert r.text == "answer from port 83\n"

def test_deep_path_not_stripped(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/deep/path/port")
    assert r.status_code == 200
    assert r.text == "answer from port 84\n"
