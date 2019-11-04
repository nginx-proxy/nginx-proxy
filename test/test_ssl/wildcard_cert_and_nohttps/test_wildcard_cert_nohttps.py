import pytest
from backports.ssl_match_hostname import CertificateError
from requests.exceptions import SSLError


@pytest.mark.parametrize("subdomain,should_redirect_to_https", [
    (1, True),
    (2, True),
    (3, False),
])
def test_http_redirects_to_https(docker_compose, nginxproxy, subdomain, should_redirect_to_https):
    r = nginxproxy.get("http://%s.web.nginx-proxy.tld/port" % subdomain)
    if should_redirect_to_https:
        assert len(r.history) > 0
        assert r.history[0].is_redirect
        assert r.history[0].headers.get("Location") == "https://%s.web.nginx-proxy.tld/port" % subdomain
    assert "answer from port 8%s\n" % subdomain == r.text


@pytest.mark.parametrize("subdomain", [1, 2])
def test_https_get_served(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("https://%s.web.nginx-proxy.tld/port" % subdomain, allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 8%s\n" % subdomain == r.text


def test_web3_https_is_500_and_SSL_validation_fails(docker_compose, nginxproxy):
    with pytest.raises( (CertificateError, SSLError) ) as excinfo:
        nginxproxy.get("https://3.web.nginx-proxy.tld/port")
    assert """hostname '3.web.nginx-proxy.tld' doesn't match 'nginx-proxy.tld'""" in str(excinfo.value)

    r = nginxproxy.get("https://3.web.nginx-proxy.tld/port", verify=False)
    assert r.status_code == 500
