def test_unknown_virtual_host_is_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx-proxy.tld/")
    assert r.status_code == 503


def test_forwards_to_whoami(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami2.nginx-proxy.tld/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami2")
    assert r.text == f"I'm {whoami_container.id[:12]}\n"
