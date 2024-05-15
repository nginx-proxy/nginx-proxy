import pytest
import requests


def test_web2_http_is_connection_refused(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 503


def test_web2_http_is_connection_refused_for_acme_challenge(
    docker_compose, nginxproxy, acme_challenge_path
):
    r = nginxproxy.get(f"http://web2.nginx-proxy.tld/{acme_challenge_path}", allow_redirects=False)
    assert r.status_code == 503


def test_web2_https_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web2.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 82\n" in r.text


def test_web2_HSTS_policy_is_active(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web2.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 82\n" in r.text
    assert "Strict-Transport-Security" in r.headers
