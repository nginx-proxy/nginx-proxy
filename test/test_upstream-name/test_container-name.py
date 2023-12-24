import pytest
import re


def test_single_container_in_upstream(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode()
    assert re.search(r"upstream web1~ \{", conf)

def test_multiple_containers_in_upstream(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode()
    assert re.search(r"upstream web2~web3~ \{", conf)

def test_no_redundant_upstreams(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode()
    assert len(re.findall(r"upstream web4~ \{", conf)) == 1

def test_valid_upstream_name(docker_compose, nginxproxy):
    """nginx should not choke on the tilde character."""
    r = nginxproxy.get("http://web1.nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 80\n"
