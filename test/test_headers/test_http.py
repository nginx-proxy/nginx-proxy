import pytest

def test_arbitrary_headers_are_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'Foo': 'Bar'})
    assert r.status_code == 200
    assert "Foo: Bar\n" in r.text


##### Testing the handling of X-Forwarded-For #####

def test_X_Forwarded_For_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-For:" in r.text

def test_X_Forwarded_For_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'X-Forwarded-For': '1.2.3.4'})
    assert r.status_code == 200
    assert "X-Forwarded-For: 1.2.3.4, " in r.text


##### Testing the handling of X-Forwarded-Proto #####

def test_X_Forwarded_Proto_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Proto: http" in r.text

def test_X_Forwarded_Proto_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Proto': 'f00'})
    assert r.status_code == 200
    assert "X-Forwarded-Proto: f00\n" in r.text


##### Testing the handling of X-Forwarded-Port #####

def test_X_Forwarded_Port_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Port: 80\n" in r.text

def test_X_Forwarded_Port_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Port': '1234'})
    assert r.status_code == 200
    assert "X-Forwarded-Port: 1234\n" in r.text


##### Testing the handling of X-Forwarded-Ssl #####

def test_X_Forwarded_Ssl_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Ssl: off\n" in r.text

def test_X_Forwarded_Ssl_is_overwritten(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Ssl': 'f00'})
    assert r.status_code == 200
    assert "X-Forwarded-Ssl: off\n" in r.text


##### Other headers

def test_X_Real_IP_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Real-IP: " in r.text

def test_Host_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: web.nginx-proxy.tld" in r.text

def test_httpoxy_safe(docker_compose, nginxproxy):
    """
    See https://httpoxy.org/
    nginx-proxy should suppress the `Proxy` header
    """
    r = nginxproxy.get("http://web.nginx-proxy.tld/headers", headers={'Proxy': 'tcp://some.hacker.com'})
    assert r.status_code == 200
    assert "Proxy:" not in r.text
    
