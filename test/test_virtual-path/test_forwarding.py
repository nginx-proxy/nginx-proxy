import pytest

def test_root_redirects_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "http://www.nginx-proxy.tld/web1/port" == r.headers['Location']

def test_direct_access(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.nginx-proxy.tld/web1/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text

def test_root_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.nginx-proxy.tld/port", allow_redirects=True)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text

