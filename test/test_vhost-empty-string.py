import re


def test_vhost_empty_string(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode()
    assert re.search(r"(?m)^\s*server_name\s+web2\.nginx-proxy\.test\s*;", conf)
    assert re.search(r"(?m)^\s*server_name\s+web3\.nginx-proxy\.test\s*;", conf)
    assert re.search(r"(?m)^\s*server_name\s+web4a\.nginx-proxy\.test\s*;", conf)
    assert re.search(r"(?m)^\s*server_name\s+web4b\.nginx-proxy\.test\s*;", conf)
    assert not re.search(r"(?m)^\s*server_name\s*;", conf)
