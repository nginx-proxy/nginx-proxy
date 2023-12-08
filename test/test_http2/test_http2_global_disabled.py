import pytest
import re

def test_http2_global_disabled_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://http2-global-disabled.nginx-proxy.tld")
    assert r.status_code == 200
    assert not re.search(r"(?s)http2-global-disabled\.nginx-proxy\.tld.*http2 on", conf)
