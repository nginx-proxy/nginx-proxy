def test_virtual_config_global_directives(docker_compose, nginxproxy):
    """Global VIRTUAL_* directives should be rendered in http block"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    config = nginxproxy.get_conf().decode('utf-8')
    
    # Global directives in http block
    assert "client_max_body_size 100m;" in config
    assert "keepalive_timeout 120s;" in config
    assert "keepalive_requests 500;" in config
