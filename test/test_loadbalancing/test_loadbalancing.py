import re


def test_loadbalance_hash(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r1 = nginxproxy.get("http://loadbalance-enabled.nginx-proxy.tld")
    r2 = nginxproxy.get("http://loadbalance-enabled.nginx-proxy.tld")
    assert re.search(r"hash \$remote_addr\;", conf)
    assert r1.status_code == 200
    assert r2.text == r1.text

def test_loadbalance_roundrobin(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://loadbalance-disabled.nginx-proxy.tld")
    r2 = nginxproxy.get("http://loadbalance-disabled.nginx-proxy.tld")
    assert r1.status_code == 200
    assert r2.text != r1.text
