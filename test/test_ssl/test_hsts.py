import pytest


def test_web1_HSTS_default(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web1.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=31536000" == r.headers["Strict-Transport-Security"]

def test_web2_HSTS_off(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web2.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" not in r.headers

def test_web3_HSTS_custom(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web3.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=86400; includeSubDomains; preload" == r.headers["Strict-Transport-Security"]
