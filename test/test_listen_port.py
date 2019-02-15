import pytest


@pytest.mark.parametrize("subdomain", ["foo", "bar"])
def test_web1_http_custom_port(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get("http://%s.nginx-proxy.tld:8080/port" % subdomain, allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text
