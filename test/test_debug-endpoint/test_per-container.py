import json

import pytest


def test_debug_endpoint_is_disabled_globally(docker_compose, nginxproxy):
    r = nginxproxy.get("http://disabled1.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 404 
    r = nginxproxy.get("http://disabled2.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 404 


def test_debug_endpoint_is_enabled_per_container(docker_compose, nginxproxy):
    r = nginxproxy.get("http://enabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200


def test_debug_endpoint_response_contains_expected_values(docker_compose, nginxproxy):   
    r = nginxproxy.get("http://enabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse debug endpoint response as JSON:: %s" % err, pytrace=False)
    assert jsonResponse["global"]["enable_debug_endpoint"] == "false"
    assert jsonResponse["vhost"]["enable_debug_endpoint"] == True
