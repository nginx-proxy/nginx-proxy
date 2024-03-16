import pytest

def test_network_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.example/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"
    assert "X-network" in r.headers
    assert "internal" == r.headers["X-network"]

def test_network_web2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.example/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 82\n"
    assert "X-network" not in r.headers
