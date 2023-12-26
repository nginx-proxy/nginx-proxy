import re


def test_keepalive_disabled(docker_compose, nginxproxy):
    r = nginxproxy.get("http://keepalive-disabled.nginx-proxy.test/headers")
    assert r.status_code == 200
    assert re.search(fr'(?m)^(?i:Connection): close$', r.text)

def test_keepalive_disabled_other_headers_ok(docker_compose, nginxproxy):
    """Make sure the other proxy_set_header headers are still set.

    According to the nginx docs [1], any proxy_set_header directive in a block
    disables inheritance of proxy_set_header directives in a parent block.  Make
    sure that doesn't happen.

    [1] https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header
    """
    r = nginxproxy.get("http://keepalive-disabled.nginx-proxy.test/headers")
    assert r.status_code == 200
    assert re.search(fr'(?m)^(?i:X-Real-IP): ', r.text)

def test_keepalive_enabled(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"keepalive 64\;", conf)

    r = nginxproxy.get("http://keepalive-enabled.nginx-proxy.test/headers")
    assert r.status_code == 200
    assert not re.search(fr'(?m)^(?i:Connection):', r.text)

def test_keepalive_auto_enabled(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"keepalive 8\;", conf)

    r = nginxproxy.get("http://keepalive-auto.nginx-proxy.test/headers")
    assert r.status_code == 200
    assert not re.search(fr'(?m)^(?i:Connection):', r.text)

def test_keepalive_enabled_other_headers_ok(docker_compose, nginxproxy):
    """See the docstring for the disabled case above."""
    r = nginxproxy.get("http://keepalive-enabled.nginx-proxy.test/headers")
    assert r.status_code == 200
    assert re.search(fr'(?m)^(?i:X-Real-IP): ', r.text)
