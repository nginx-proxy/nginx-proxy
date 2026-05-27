def test_virtual_config_invalid_values_ignored(docker_compose, nginxproxy):
    """Invalid VIRTUAL_* values should be silently ignored due to format validation"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    config = nginxproxy.get_conf().decode('utf-8')
    
    # Valid value should be present
    assert "client_max_body_size 100m;" in config
    
    # Invalid values should NOT appear (silently ignored)
    assert "keepalive_timeout invalid_value;" not in config
    assert "keepalive_requests not_a_number;" not in config
    assert "proxy_buffering maybe;" not in config
    assert "client_header_buffer_size not_a_size;" not in config
    assert "real_ip_recursive yes_or_no;" not in config
