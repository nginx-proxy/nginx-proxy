import pytest
import re


def test_custom_error_page(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx-proxy.tld")
    assert r.status_code == 503
    assert re.search(r"Damn, there's some maintenance in progress.", r.text)
