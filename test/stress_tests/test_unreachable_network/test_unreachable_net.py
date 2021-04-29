from time import sleep

import pytest
import requests

pytestmark = pytest.mark.xfail()  # TODO delete this marker once #585 is merged


def test_default_nginx_welcome_page_should_not_be_served(docker_compose, nginxproxy):
    r = nginxproxy.get("http://whatever.nginx-proxy/", allow_redirects=False)
    assert "<title>Welcome to nginx!</title>" not in r.text


def test_unknown_virtual_host_is_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://unknown.nginx-proxy/", allow_redirects=False)
    assert r.status_code == 503


def test_http_web_a_is_forwarded(docker_compose, nginxproxy):
    r = nginxproxy.get("http://webA.nginx-proxy/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" == r.text


def test_http_web_b_gets_an_error(docker_compose, nginxproxy):
    r = nginxproxy.get("http://webB.nginx-proxy/", allow_redirects=False)
    assert "<title>Welcome to nginx!</title>" not in r.text
    with pytest.raises(requests.exceptions.HTTPError):
        r.raise_for_status()


def test_reverseproxy_survive_restart(docker_compose):
    docker_compose.containers.get("reverseproxy").restart()
    sleep(2)  # give time for the container to initialize
    assert docker_compose.containers.get("reverseproxy").status == "running"
