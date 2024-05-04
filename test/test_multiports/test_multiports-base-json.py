import pytest


def test_virtual_host_is_dropped_when_using_multiports(docker_compose, nginxproxy):
    r = nginxproxy.get("http://notskipped.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text
    r = nginxproxy.get("http://skipped.nginx-proxy.tld/")
    assert r.status_code == 503


def test_answer_is_served_from_port_80_by_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://port80.a.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text
    r = nginxproxy.get("http://port80.b.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text
    r = nginxproxy.get("http://port80.c.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text


def test_answer_is_served_from_chosen_ports(docker_compose, nginxproxy):
    r = nginxproxy.get("http://port8080.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 8080\n" in r.text
    r = nginxproxy.get("http://port9000.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 9000\n" in r.text


def test_answer_is_served_from_chosen_ports_and_dest(docker_compose, nginxproxy):
    r = nginxproxy.get("http://virtualpaths.nginx-proxy.tld/rootdest/port")
    assert r.status_code == 200
    assert "answer from port 10001\n" in r.text
    r = nginxproxy.get("http://virtualpaths.nginx-proxy.tld/customdest")
    assert r.status_code == 200
    assert "answer from port 10002\n" in r.text
