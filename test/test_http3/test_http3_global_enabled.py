import pytest
import re

    #Python Requests is not able to do native http3 requests. 
    #We only check for directives which should enable http3.

def test_http3_global_enabled_ALTSVC_header(docker_compose, nginxproxy):
    r = nginxproxy.get("http://http3-global-enabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: http3-global-enabled.nginx-proxy.tld" in r.text
    assert "alt-svc" in r.headers
    assert r.headers["alt-svc"] == 'h3=":443"; ma=86400;'

def test_http3_global_enabled_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http3-global-enabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert re.search(r"listen 443 quic reuseport\;", conf)
    assert re.search(r"(?s)http3-global-enabled\.nginx-proxy\.tld;.*listen 443 quic", conf)
    assert re.search(r"(?s)http3-global-enabled\.nginx-proxy\.tld;.*http3 on\;", conf)
    assert re.search(r"(?s)http3-global-enabled\.nginx-proxy\.tld;.*add_header alt-svc \'h3=\":443\"; ma=86400;\'", conf)
