import pytest


@pytest.mark.parametrize("host,http_method,expected_code", [
    ("nginx-proxy.tld", "GET", 301),
    ("nginx-proxy.tld", "HEAD", 301),
    ("nginx-proxy.tld", "POST", 308),
    ("nginx-proxy.tld", "PUT", 308),
    ("nginx-proxy.tld", "PATCH", 308),
    ("nginx-proxy.tld", "DELETE", 308),
    ("nginx-proxy.tld", "OPTIONS", 308),
    ("nginx-proxy.tld", "CONNECT", 405),
    ("nginx-proxy.tld", "TRACE", 405),
    ("web2.nginx-proxy.tld", "GET", 301),
    ("web2.nginx-proxy.tld", "HEAD", 301),
    ("web2.nginx-proxy.tld", "POST", 307),
    ("web2.nginx-proxy.tld", "PUT", 307),
    ("web2.nginx-proxy.tld", "PATCH", 307),
    ("web2.nginx-proxy.tld", "DELETE", 307),
    ("web2.nginx-proxy.tld", "OPTIONS", 307),
    ("web2.nginx-proxy.tld", "CONNECT", 405),
    ("web2.nginx-proxy.tld", "TRACE", 405),
])
def test_custom_redirect_by_method(
    docker_compose,
    nginxproxy,
    host: str,
    http_method: str,
    expected_code: int,
):
    r = nginxproxy.request(
        method=http_method,
        url=f'http://{host}',
        allow_redirects=False,
    )
    assert r.status_code == expected_code
    if expected_code in { 301, 302, 307, 308 }:
        assert r.headers['Location'] == f'https://{host}/'
