import pytest

def test_htpasswd_virtual_host_is_restricted(docker_compose, nginxproxy):
    r = nginxproxy.get("http://htpasswd.nginx-proxy.tld/port")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
    assert r.headers["WWW-Authenticate"] == 'Basic realm="Restricted htpasswd.nginx-proxy.tld"'


def test_htpasswd_virtual_host_basic_auth(docker_compose, nginxproxy):
    r = nginxproxy.get("http://htpasswd.nginx-proxy.tld/port", auth=("vhost", "password"))
    assert r.status_code == 200
    assert r.text == "answer from port 80\n"
