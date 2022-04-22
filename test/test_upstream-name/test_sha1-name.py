import pytest
import re


def test_sha1_upstream_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"upstream 3e837201a6255962094cd6d8f61e22b07d3cc8ed \{", conf)

def test_sha1_upstream_forwards_correctly(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 80\n"
