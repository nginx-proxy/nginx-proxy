import pytest


def test_web_no_slash_location(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 405

def test_web_rout_to_slash_port(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/which-port")
    assert r.status_code == 200
    assert "answer from port 83\n" in r.text

def test_web1_answers_on_slash_location(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/")
    assert r.status_code == 200

def test_web1_no_virtual_path(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/which-port")
    assert r.status_code == 404

def test_web1_port_80_is_served_by_location_slash_80(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/80/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text

def test_web1_port_81_is_served_by_location_slash_81(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld/81/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text
