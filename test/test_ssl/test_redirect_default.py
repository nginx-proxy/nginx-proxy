import pytest


@pytest.mark.parametrize("http_method,expected_code", [
    ("GET", 301),
    ("HEAD", 301),
    ("POST", 301),
    ("PUT", 301),
    ("PATCH", 301),
    ("DELETE", 301),
    ("OPTIONS", 301),
    ("CONNECT", 405),
    ("TRACE", 405),
])
def test_default_redirect_by_method(
    docker_compose,
    nginxproxy,
    http_method: str,
    expected_code: int,
):
    r = nginxproxy.request(
        method=http_method,
        url='http://nginx-proxy.tld',
        allow_redirects=False,
    )
    assert r.status_code == expected_code
    if expected_code in { 301, 302, 307, 308 }:
        assert r.headers['Location'] == 'https://nginx-proxy.tld/'
