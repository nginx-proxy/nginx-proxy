import pytest

def test_default_root_response(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/")
    assert r.status_code == 418

@pytest.mark.parametrize("stub,header", [
    ("nginx-proxy.test/web1", "bar"),
    ("foo.nginx-proxy.test", "f00"),
])
def test_custom_applies(docker_compose, nginxproxy, stub, header):
    r = nginxproxy.get(f"http://{stub}/port")
    assert r.status_code == 200
    assert "X-test" in r.headers
    assert header == r.headers["X-test"]

@pytest.mark.parametrize("stub,code", [
    ("nginx-proxy.test/foo", 418),
    ("nginx-proxy.test/web2", 200),
    ("nginx-proxy.test/web3", 200),
    ("bar.nginx-proxy.test", 503),
])
def test_custom_does_not_apply(docker_compose, nginxproxy, stub, code):
    r = nginxproxy.get(f"http://{stub}/port")
    assert r.status_code == code
    assert "X-test" not in r.headers

@pytest.mark.parametrize("stub,port", [
    ("nginx-proxy.test/web1", 81),
    ("nginx-proxy.test/web2", 82),
    ("nginx-proxy.test/web3", 83),
    ("nginx-proxy.test/alt", 83),
])
def test_alternate(docker_compose, nginxproxy, stub, port):
    r = nginxproxy.get(f"http://{stub}/port")
    assert r.status_code == 200
    assert r.text == f"answer from port {port}\n"

