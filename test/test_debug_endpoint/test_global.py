import json
import pytest

def test_debug_endpoint_is_enabled_globally(docker_compose, nginxproxy):
    r = nginxproxy.get("http://enabled1.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    r = nginxproxy.get("http://enabled2.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200


def test_debug_endpoint_response_contains_expected_values(docker_compose, nginxproxy):   
    r = nginxproxy.get("http://enabled1.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse JSON response: %s" % err, pytrace=False)
    assert jsonResponse["global"]["enable_debug_endpoint"] == "true"
    assert jsonResponse["vhost"]["enable_debug_endpoint"] == True


def test_debug_endpoint_is_disabled_per_container(docker_compose, nginxproxy):
    r = nginxproxy.get("http://disabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 404  
