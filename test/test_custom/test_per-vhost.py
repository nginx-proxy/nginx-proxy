import pytest

def test_custom_conf_does_not_apply_to_unknown_vhost(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503
    assert "X-test" not in r.headers

def test_custom_conf_applies_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.example/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"
    assert "X-test" in r.headers
    assert "f00" == r.headers["X-test"]

def test_custom_conf_does_not_apply_to_web2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.example/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 82\n"
    assert "X-test" not in r.headers
