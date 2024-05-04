import pytest


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_http_redirects_to_https(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get(f"http://{subdomain}.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert f"https://{subdomain}.nginx-proxy.tld/" == r.headers['Location']


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_https_is_forwarded(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get(f"https://{subdomain}.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_HSTS_policy_is_active(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get(f"https://{subdomain}.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_acme_challenge_works(docker_compose, nginxproxy, acme_challenge_path, subdomain):
    r = nginxproxy.get(
        f"http://web3.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 200
    assert "challenge-teststring\n" in r.text
