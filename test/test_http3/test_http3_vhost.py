import pytest
import re

    #Python Requests is not able to do native http3 requests. 
    #We only check for directives which should enable http3.

def test_http3_vhost_enabled_ALTSVC_header(docker_compose, nginxproxy):
    r = nginxproxy.get("http://http3-vhost-enabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: http3-vhost-enabled.nginx-proxy.tld" in r.text
    assert "alt-svc" in r.headers
    assert r.headers["alt-svc"] == 'h3=":443"; ma=86400;'

def test_http3_vhost_enabled_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http3-vhost-enabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert re.search(r"listen 443 quic reuseport\;", conf)
    assert re.search(r"(?s)http3-vhost-enabled\.nginx-proxy\.tld;.*listen 443 quic", conf)
    assert re.search(r"(?s)http3-vhost-enabled\.nginx-proxy\.tld;.*http3 on\;", conf)
    assert re.search(r"(?s)http3-vhost-enabled\.nginx-proxy\.tld;.*add_header alt-svc \'h3=\":443\"; ma=86400;\'", conf)

def test_http3_vhost_disabled_ALTSVC_header(docker_compose, nginxproxy):
    r = nginxproxy.get("http://http3-vhost-disabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: http3-vhost-disabled.nginx-proxy.tld" in r.text
    assert not "alt-svc" in r.headers

def test_http3_vhost_disabled_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http3-vhost-disabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert not re.search(r"(?s)http3-vhost-disabled\.nginx-proxy\.tld.*listen 443 quic.*\# http3-vhost-enabled\.nginx-proxy\.tld", conf)
    assert not re.search(r"(?s)http3-vhost-disabled\.nginx-proxy\.tld.*http3 on.*\# http3-vhost-enabled\.nginx-proxy\.tld", conf)
    assert not re.search(r"(?s)http3-vhost-disabled\.nginx-proxy\.tld;.*add_header alt-svc \'h3=\":443\"; ma=86400;\'.*\# http3-vhost-enabled\.nginx-proxy\.tld", conf)

def test_http3_vhost_disabledbydefault_ALTSVC_header(docker_compose, nginxproxy):
    r = nginxproxy.get("http://http3-vhost-default-disabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "Host: http3-vhost-default-disabled.nginx-proxy.tld" in r.text
    assert not "alt-svc" in r.headers

def test_http3_vhost_disabledbydefault_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http3-vhost-default-disabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert not re.search(r"(?s)http3-vhost-default-disabled\.nginx-proxy\.tld.*listen 443 quic.*\# http3-vhost-disabled\.nginx-proxy\.tld", conf)
    assert not re.search(r"(?s)http3-vhost-default-disabled\.nginx-proxy\.tld.*http3 on.*\# http3-vhost-disabled\.nginx-proxy\.tld", conf)
    assert not re.search(r"(?s)http3-vhost-default-disabled\.nginx-proxy\.tld;.*add_header alt-svc \'h3=\":443\"; ma=86400;\'.*\# http3-vhost-disabled\.nginx-proxy\.tld", conf)
