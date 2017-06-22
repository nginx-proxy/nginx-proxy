from time import sleep


def test_nginx_is_running(nginx_tmpl, docker_compose):
    sleep(3)
    assert docker_compose.containers.get("nginx").status == "running"


def test_unknown_virtual_host_is_503(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx.container.docker/")
    assert r.status_code == 503


def test_forwards_to_whoami(nginx_tmpl, docker_compose, nginxproxy):
    r = nginxproxy.get("http://whoami.nginx.container.docker/")
    assert r.status_code == 200
    whoami_container = docker_compose.containers.get("whoami")
    assert r.text == "I'm %s\n" % whoami_container.id[:12]
