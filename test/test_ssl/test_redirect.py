import pytest

# These tests are to test that GET is 301 and other methods all use 308
# Permanent Redirects
# https://github.com/nginx-proxy/nginx-proxy/pull/1737
def test_web1_GET_301(docker_compose, nginxproxy):
    r = nginxproxy.get('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 301
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'

def test_web1_POST_308(docker_compose, nginxproxy):
    r = nginxproxy.post('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 308
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'

def test_web1_PUT_308(docker_compose, nginxproxy):
    r = nginxproxy.put('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 308
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'

def test_web1_HEAD_308(docker_compose, nginxproxy):
    r = nginxproxy.head('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 308
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'

def test_web1_DELETE_308(docker_compose, nginxproxy):
    r = nginxproxy.delete('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 308
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'

def test_web1_OPTIONS_308(docker_compose, nginxproxy):
    r = nginxproxy.options('http://web1.nginx-proxy.tld', allow_redirects=False)
    assert r.status_code == 308
    assert r.headers['Location'] == 'https://web1.nginx-proxy.tld/'
