import pytest


def test_answer_is_served_from_exposed_port_even_if_not_80(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text
