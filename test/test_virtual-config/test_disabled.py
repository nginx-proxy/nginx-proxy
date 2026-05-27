def test_virtual_config_disabled_by_default(docker_compose, nginxproxy):
    """When ENABLE_VIRTUAL_CONFIG is not set, VIRTUAL_* directives should be ignored"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    # Check that the config was generated but virtual directives were not applied
    config = nginxproxy.get_conf().decode('utf-8')
    
    # These directives should NOT appear in the http block since the feature is disabled
    assert "client_max_body_size 50m;" not in config
    assert "keepalive_timeout 60s;" not in config
