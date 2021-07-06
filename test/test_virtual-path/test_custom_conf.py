import pytest

def test_default_root_response(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/")
    assert r.status_code == 418

