import pytest


def test_answer_is_served_from_port_80_by_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text
