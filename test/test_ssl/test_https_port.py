import pytest

@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_http_redirects_to_https(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("http://%s.nginx-proxy.tld:8080/" % subdomain, allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://%s.nginx-proxy.tld:8443/" % subdomain == r.headers['Location']

@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_https_is_forwarded(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("https://%s.nginx-proxy.tld:8443/port" % subdomain, allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text

def test_nonstandardport_Host_header(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld:8443/headers")
    assert r.status_code == 200
    assert "Host: web.nginx-proxy.tld:8443" in r.text

@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_acme_challenge_works(docker_compose, nginxproxy, acme_challenge_path, subdomain):
    r = nginxproxy.get(
        f"http://{subdomain}.nginx-proxy.tld:8080/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 200
    assert "challenge-teststring\n" in r.text
