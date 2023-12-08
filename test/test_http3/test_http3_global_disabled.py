import pytest
import re

    #Python Requests is not able to do native http3 requests. 
    #We only check for directives which should enable http3.

def test_http3_global_disabled_ALTSVC_header(docker_compose, nginxproxy):
    r = nginxproxy.get("http://http3-global-disabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: http3-global-disabled.nginx-proxy.tld" in r.text
    assert not "alt-svc" in r.headers

def test_http3_global_disabled_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http3-global-disabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert not re.search(r"(?s)listen 443 quic", conf)
    assert not re.search(r"(?s)http3 on", conf)
    assert not re.search(r"(?s)add_header alt-svc \'h3=\":443\"; ma=86400;\'", conf)
