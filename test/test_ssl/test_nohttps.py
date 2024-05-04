import pytest
from requests import ConnectionError

def test_http_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 83\n" in r.text


def test_https_is_disabled(docker_compose, nginxproxy):
    with pytest.raises(ConnectionError):
        nginxproxy.get("https://web.nginx-proxy.tld/", allow_redirects=False)


def test_http_acme_challenge_does_not_work(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 404
