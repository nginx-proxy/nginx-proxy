import re

import pytest


def test_unknown_virtual_host(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503

def test_forwards_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.example/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"

def test_forwards_to_web2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.example/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n"

def test_multipath(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web3.nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 83\n"
    cfg = nginxproxy.get_conf().decode()
    lines = cfg.splitlines()
    web3_server_lines = [l for l in lines
                         if re.search(r'(?m)^\s*server\s+[^\s]*:83;\s*$', l)]
    assert len(web3_server_lines) == 1
