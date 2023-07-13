import pytest


def test_arbitrary_headers_are_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'Foo': 'Bar'})
    assert r.status_code == 200
    assert "Foo: Bar\n" in r.text


##### Testing the handling of X-Forwarded-For #####

def test_X_Forwarded_For_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-For:" in r.text

def test_X_Forwarded_For_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'X-Forwarded-For': '1.2.3.4'})
    assert r.status_code == 200
    assert "X-Forwarded-For: 1.2.3.4, " in r.text


##### Testing the handling of X-Forwarded-Proto #####

def test_X_Forwarded_Proto_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Proto: https" in r.text

def test_X_Forwarded_Proto_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Proto': 'f00'})
    assert r.status_code == 200
    assert "X-Forwarded-Proto: f00\n" in r.text


##### Testing the handling of X-Forwarded-Host #####

def test_X_Forwarded_Host_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Host: web.nginx-proxy.tld\n" in r.text

def test_X_Forwarded_Host_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Host': 'example.com'})
    assert r.status_code == 200
    assert "X-Forwarded-Host: example.com\n" in r.text


##### Testing the handling of X-Forwarded-Port #####

def test_X_Forwarded_Port_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Port: 443\n" in r.text

def test_X_Forwarded_Port_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Port': '1234'})
    assert r.status_code == 200
    assert "X-Forwarded-Port: 1234\n" in r.text


##### Testing the handling of X-Forwarded-Ssl #####

def test_X_Forwarded_Ssl_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Ssl: on\n" in r.text

def test_X_Forwarded_Ssl_is_overwritten(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'X-Forwarded-Ssl': 'f00'})
    assert r.status_code == 200
    assert "X-Forwarded-Ssl: on\n" in r.text


##### Other headers

def test_X_Real_IP_is_generated(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Real-IP: " in r.text

def test_Host_is_passed_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: web.nginx-proxy.tld" in r.text

def test_httpoxy_safe(docker_compose, nginxproxy):
    """
    See https://httpoxy.org/
    nginx-proxy should suppress the `Proxy` header
    """
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers", headers={'Proxy': 'tcp://some.hacker.com'})
    assert r.status_code == 200
    assert "Proxy:" not in r.text


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_no_host_server_tokens_off(docker_compose, nginxproxy):
    ip = nginxproxy.get_ip()
    r = nginxproxy.get(f"https://{ip}/headers", verify=False)
    assert r.status_code == 503
    assert r.headers["Server"] == "nginx"


def test_server_tokens_on(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: web.nginx-proxy.tld" in r.text
    assert r.headers["Server"].startswith("nginx/")


def test_server_tokens_off(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web-server-tokens-off.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: web-server-tokens-off.nginx-proxy.tld" in r.text
    assert r.headers["Server"] == "nginx"
