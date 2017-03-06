import pytest

def test_unknown_virtual_host(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503

def test_forwards_to_whoami(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.local/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"
