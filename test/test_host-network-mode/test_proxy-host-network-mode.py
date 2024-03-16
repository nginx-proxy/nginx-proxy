import pytest


def test_forwards_to_host_network_container_1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://host-network-1.nginx-proxy.tld:8888/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8080\n"


def test_forwards_to_host_network_container_2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://host-network-2.nginx-proxy.tld:8888/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8181\n"
