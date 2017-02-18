import pytest


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_http_redirects_to_https(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("http://%s.nginx-proxy.tld/" % subdomain, allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://%s.nginx-proxy.tld/" % subdomain == r.headers['Location']


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_https_is_forwarded(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("https://%s.nginx-proxy.tld/port" % subdomain, allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_HSTS_policy_is_active(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("https://%s.nginx-proxy.tld/port" % subdomain, allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
