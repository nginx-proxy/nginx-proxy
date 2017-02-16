import pytest
from requests import ConnectionError


def test_unknown_virtual_host(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/port")
    assert r.status_code == 503


def test_forwards_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"


def test_forwards_to_web2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n" 


def test_ipv6_is_disabled_by_default(docker_compose, nginxproxy):
    with pytest.raises(ConnectionError):
        nginxproxy.get("http://nginx-proxy/port", ipv6=True)
