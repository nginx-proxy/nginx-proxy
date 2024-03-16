import pytest


def test_forwards_to_bridge_network_container(docker_compose, nginxproxy):
    r = nginxproxy.get("http://bridge-network.nginx-proxy.tld/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 80\n"


def test_forwards_to_host_network_container(docker_compose, nginxproxy):
    r = nginxproxy.get("http://host-network.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8080\n" 
