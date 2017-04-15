import pytest


def test_web3_http_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web3.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 83\n" in r.text


def test_web3_https_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web3.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 83\n" in r.text


def test_web2_HSTS_policy_is_inactive(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web3.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 83\n" in r.text
    assert "Strict-Transport-Security" not in r.headers