import pytest


def test_web1_is_backup(docker_compose, nginxproxy):
    for i in range(1, 10):
        r = nginxproxy.get("http://web1.nginx-proxy.tld/port")
        assert r.status_code == 200
        assert r.text == "answer from port 91\n"

def test_web2_is_production(docker_compose, nginxproxy):
    for i in range(1, 10):
        r = nginxproxy.get("http://web2.nginx-proxy.tld/port")
        assert r.status_code == 200
        assert r.text == "answer from port 82\n"
