import pytest

@pytest.mark.parametrize("path", ["web1", "web2"])
def test_web1_http_redirects_to_https(docker_compose, nginxproxy, path):
    r = nginxproxy.get("http://www.nginx-proxy.tld/%s/port" % path, allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://www.nginx-proxy.tld/%s/port" % path == r.headers['Location']

@pytest.mark.parametrize("path,port", [("web1", 81), ("web2", 82)])
def test_web1_https_is_forwarded(docker_compose, nginxproxy, path, port):
    r = nginxproxy.get("https://www.nginx-proxy.tld/%s/port" % path, allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port %d\n" % port in r.text

