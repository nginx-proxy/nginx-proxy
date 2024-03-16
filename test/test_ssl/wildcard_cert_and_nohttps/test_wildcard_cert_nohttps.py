import pytest
from ssl import CertificateError
from requests.exceptions import SSLError


@pytest.mark.parametrize("subdomain,should_redirect_to_https", [
    (1, True),
    (2, True),
    (3, False),
])
def test_http_redirects_to_https(docker_compose, nginxproxy, subdomain, should_redirect_to_https):
    r = nginxproxy.get(f"http://{subdomain}.web.nginx-proxy.tld/port")
    if should_redirect_to_https:
        assert len(r.history) > 0
        assert r.history[0].is_redirect
        assert r.history[0].headers.get("Location") == f"https://{subdomain}.web.nginx-proxy.tld/port"
    assert f"answer from port 8{subdomain}\n" == r.text


@pytest.mark.parametrize("subdomain", [1, 2])
def test_https_get_served(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get(f"https://{subdomain}.web.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert f"answer from port 8{subdomain}\n" == r.text

@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_https_request_to_nohttps_vhost_goes_to_fallback_server(docker_compose, nginxproxy):
    with pytest.raises( (CertificateError, SSLError) ) as excinfo:
        nginxproxy.get("https://3.web.nginx-proxy.tld/port")
    assert """certificate is not valid for '3.web.nginx-proxy.tld'""" in str(excinfo.value) or \
           """hostname '3.web.nginx-proxy.tld' doesn't match 'nginx-proxy.tld'""" in str(excinfo.value)

    r = nginxproxy.get("https://3.web.nginx-proxy.tld/port", verify=False)
    assert r.status_code == 503
