import json
import pytest


@pytest.mark.parametrize("host,expected_cert_ok,expected_cert", [
    ("nginx-proxy.tld", True, "nginx-proxy.tld"),
    ("web1.nginx-proxy.tld", True, "nginx-proxy.tld"),
    ("sub.web1.nginx-proxy.tld", False, ""),
    ("web2.nginx-proxy.tld", True, "web2.nginx-proxy.tld"),
])
def test_certificate_selection(
    docker_compose,
    nginxproxy,
    host: str,
    expected_cert_ok: bool,
    expected_cert: str,
):
    r = nginxproxy.get(f"http://{host}/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse debug endpoint response as JSON:: %s" % err, pytrace=False)
    assert jsonResponse["vhost"]["cert_ok"] == expected_cert_ok
    assert jsonResponse["vhost"]["cert"] == expected_cert
