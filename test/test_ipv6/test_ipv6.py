import pytest


def test_unknown_virtual_host_ipv4(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/port")
    assert r.status_code == 503


def test_forwards_to_web1_ipv4(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"


def test_forwards_to_web2_ipv4(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n" 


def test_unknown_virtual_host_ipv6(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/port", ipv6=True)
    assert r.status_code == 503


def test_forwards_to_web1_ipv6(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/port", ipv6=True)
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"


def test_forwards_to_web2_ipv6(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.tld/port", ipv6=True)
    assert r.status_code == 200
    assert r.text == "answer from port 82\n" 
