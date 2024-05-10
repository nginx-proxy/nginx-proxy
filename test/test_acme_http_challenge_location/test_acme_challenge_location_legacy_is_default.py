import pytest


def test_redirect_acme_challenge_location_legacy(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web1.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 200

def test_noderirect_acme_challenge_location_legacy(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web2.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 404
