import pytest


def test_nohttp_missing_cert_disabled(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nohttp-missing-cert-disabled.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 503

def test_nohttp_missing_cert_enabled(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nohttp-missing-cert-enabled.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 200

def test_redirect_missing_cert_disabled(docker_compose, nginxproxy):
    r = nginxproxy.get("http://redirect-missing-cert-disabled.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 301

def test_redirect_missing_cert_enabled(docker_compose, nginxproxy):
    r = nginxproxy.get("http://redirect-missing-cert-enabled.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 200
