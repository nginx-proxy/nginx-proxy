import pytest

def test_location_precedence_case1(docker_compose, nginxproxy):
    r = nginxproxy.get(f"http://foo.nginx-proxy.test/web1/port")
    assert r.status_code == 200

    assert "X-test-default" in r.headers
    assert "X-test-host" not in r.headers
    assert "X-test-path" not in r.headers

    assert r.headers["X-test-default"] == "true"

def test_location_precedence_case2(docker_compose, nginxproxy):
    r = nginxproxy.get(f"http://bar.nginx-proxy.test/web2/port")
    assert r.status_code == 200

    assert "X-test-default" not in r.headers
    assert "X-test-host" in r.headers
    assert "X-test-path" not in r.headers

    assert r.headers["X-test-host"] == "true"

def test_location_precedence_case3(docker_compose, nginxproxy):
    r = nginxproxy.get(f"http://bar.nginx-proxy.test/web3/port")
    assert r.status_code == 200

    assert "X-test-default" not in r.headers
    assert "X-test-host" not in r.headers
    assert "X-test-path" in r.headers

    assert r.headers["X-test-path"] == "true"

