import pytest

def test_forwards_to_whoami1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.local/web1")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami1")
    assert r.text == "I'm %s\n" % whoami_container.id[:12]

def test_forwards_to_whoami2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.local/web2")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami2")
    assert r.text == "I'm %s\n" % whoami_container.id[:12]

def test_forwards_to_status(docker_compose, nginxproxy):
    r = nginxproxy.get("http://status.nginx-proxy.local/status/418")
    assert r.status_code == 418
    assert r.text == "answer with response code 418\n"

def test_forwards_to_unknown1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.local/foo")
    assert r.status_code == 503

def test_forwards_to_unknown2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.local/")
    assert r.status_code == 503
