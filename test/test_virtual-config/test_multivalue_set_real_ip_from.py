def test_virtual_config_multivalue_set_real_ip_from_global(docker_compose, nginxproxy):
    """Global VIRTUAL_SET_REAL_IP_FROM with semicolon-separated values should create multiple directives"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    config = nginxproxy.get_conf().decode('utf-8')
    
    # Each value should be a separate set_real_ip_from directive
    assert "set_real_ip_from 10.0.0.0/8;" in config
    assert "set_real_ip_from 172.16.0.0/12;" in config
    assert "set_real_ip_from 192.168.0.0/16;" in config
    
    # Other real_ip directives should also be present
    assert "real_ip_header X-Forwarded-For;" in config
    assert "real_ip_recursive on;" in config


def test_virtual_config_multivalue_set_real_ip_from_per_vhost(docker_compose, nginxproxy):
    """Per-vhost VIRTUAL_SET_REAL_IP_FROM with semicolon-separated values"""
    r = nginxproxy.get("http://web.nginx-proxy.tld/")
    assert r.status_code == 200
    
    config = nginxproxy.get_conf().decode('utf-8')
    
    # Per-vhost directives should have separate set_real_ip_from lines
    assert "set_real_ip_from 127.0.0.1;" in config
    assert "set_real_ip_from ::1;" in config
