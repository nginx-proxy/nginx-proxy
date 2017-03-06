import pytest


@pytest.mark.parametrize("host,expected_port", [
    ("f00.nginx-proxy.test", 81),
    ("bar.nginx-proxy.test", 81),
    ("test.nginx-proxy.f00", 82),
    ("test.nginx-proxy.bar", 82),
    ("web3.123.nginx-proxy.regexp", 83),
    ("web3.ABC.nginx-proxy.regexp", 83),
    ("web3.123.ABC.nginx-proxy.regexp", 83),
    ("web3.123-ABC.nginx-proxy.regexp", 83),
    ("web3.whatever.nginx-proxy.regexp-to-infinity-and-beyond", 83),
    ("web4.123.nginx-proxy.regexp", 84),
    ("web4.ABC.nginx-proxy.regexp", 84),
    ("web4.123.ABC.nginx-proxy.regexp", 84),
    ("web4.123-ABC.nginx-proxy.regexp", 84),
    ("web4.whatever.nginx-proxy.regexp", 84),
])
def test_wildcard_prefix(docker_compose, nginxproxy, host, expected_port):
    r = nginxproxy.get("http://%s/port" % host)
    assert r.status_code == 200
    assert r.text == "answer from port %s\n" % expected_port


@pytest.mark.parametrize("host", [
    "unexpected.nginx-proxy.tld",
    "web4.whatever.nginx-proxy.regexp-to-infinity-and-beyond"
])
def test_non_matching_host_is_503(docker_compose, nginxproxy, host):
    r = nginxproxy.get("http://%s/port" % host)
    assert r.status_code == 503, r.text
