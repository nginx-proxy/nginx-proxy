import pytest


def test_web1_HSTS_default(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web1.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=31536000" == r.headers["Strict-Transport-Security"]

# Regression test to ensure HSTS is enabled even when the upstream sends an error in response
# Issue #1073 https://github.com/nginx-proxy/nginx-proxy/pull/1073
def test_web1_HSTS_error(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web1.nginx-proxy.tld/status/500", allow_redirects=False)
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=31536000" == r.headers["Strict-Transport-Security"]

def test_web2_HSTS_off(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web2.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" not in r.headers

def test_web3_HSTS_custom(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web3.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=86400; includeSubDomains; preload" == r.headers["Strict-Transport-Security"]

# Regression test for issue 1080
# https://github.com/nginx-proxy/nginx-proxy/issues/1080
def test_web4_HSTS_off_noredirect(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web4.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" not in r.headers

def test_http3_vhost_enabled_HSTS_default(docker_compose, nginxproxy):
    r = nginxproxy.get("https://http3-vhost-enabled.nginx-proxy.tld/port", allow_redirects=False)
    assert "answer from port 81\n" in r.text
    assert "Strict-Transport-Security" in r.headers
    assert "max-age=31536000" == r.headers["Strict-Transport-Security"]
    assert "alt-svc" in r.headers
    assert r.headers["alt-svc"] == 'h3=":443"; ma=86400;'
