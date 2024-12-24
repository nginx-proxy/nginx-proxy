import json

import pytest


def test_debug_endpoint_is_enabled_globally(docker_compose, nginxproxy):
    r = nginxproxy.get("http://enabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    r = nginxproxy.get("http://stripped.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200


def test_debug_endpoint_response_contains_expected_values(docker_compose, nginxproxy):   
    r = nginxproxy.get("http://enabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse debug endpoint response as JSON: %s" % err, pytrace=False)
    assert jsonResponse["global"]["enable_debug_endpoint"] == "true"
    assert jsonResponse["vhost"]["enable_debug_endpoint"] == True


def test_debug_endpoint_paths_stripped_if_response_too_long(docker_compose, nginxproxy):   
    r = nginxproxy.get("http://stripped.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse debug endpoint response as JSON: %s" % err, pytrace=False)
    if "paths" in jsonResponse["vhost"]:
        pytest.fail("Expected paths to be stripped from debug endpoint response", pytrace=False)
    assert jsonResponse["warning"] == "Virtual paths configuration for this hostname is too large and has been stripped from response."


def test_debug_endpoint_hostname_replaced_by_warning_if_regexp(docker_compose, nginxproxy):   
    r = nginxproxy.get("http://regexp.foo.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 200
    try:
        jsonResponse = json.loads(r.text)
    except ValueError as err:
        pytest.fail("Failed to parse debug endpoint response as JSON: %s" % err, pytrace=False)
    assert jsonResponse["vhost"]["hostname"] == "Hostname is a regexp and unsafe to include in the debug response."


def test_debug_endpoint_is_disabled_per_container(docker_compose, nginxproxy):
    r = nginxproxy.get("http://disabled.debug.nginx-proxy.example/nginx-proxy-debug")
    assert r.status_code == 404  
