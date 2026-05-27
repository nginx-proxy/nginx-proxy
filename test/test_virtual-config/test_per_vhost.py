def test_virtual_config_per_vhost_directives(docker_compose, nginxproxy):
    """Per-vhost VIRTUAL_* directives should be rendered in server block"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    config = nginxproxy.get_conf().decode('utf-8')
    
    # Per-vhost directives in server block for web.nginx-proxy.tld
    assert "client_max_body_size 200m;" in config
    assert "keepalive_timeout 60s;" in config
    assert "proxy_buffering off;" in config
