def test_forwards_to_ipv4_only_network(docker_compose, nginxproxy):
    r = nginxproxy.get("http://ipv4only.nginx-proxy.tld/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 80\n"


def test_forwards_to_dualstack_network(docker_compose, nginxproxy):
    r = nginxproxy.get("http://dualstack.nginx-proxy.tld")
    assert r.status_code == 200   
    assert "Welcome to nginx!" in r.text


def test_dualstack_network_prefer_ipv6_config(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert "IPv4 address: 172.16.20.2 (ignored; reachable but IPv6 prefered)" in conf
    assert "server [fd00:cafe:face:feed::2]:80;" in conf
