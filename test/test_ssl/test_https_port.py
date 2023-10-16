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