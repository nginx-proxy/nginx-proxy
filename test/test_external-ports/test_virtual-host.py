def test_web1_has_custom_http_and_https_ports(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://web1.nginx-proxy.tld:8080/port", allow_redirects=False)
    assert r1.status_code == 301
    assert r1.headers['Location'] == 'https://web1.nginx-proxy.tld:8443/port'
    
    r2 = nginxproxy.get(r1.headers['Location'], allow_redirects=False)
    assert r2.status_code == 200
    assert "answer from port 81\n" in r2.text

def test_web2_has_default_http_port_and_custom_https_port(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://web2.nginx-proxy.tld/port", allow_redirects=False)
    assert r1.status_code == 301
    assert r1.headers['Location'] == 'https://web2.nginx-proxy.tld:8443/port'

    r2 = nginxproxy.get(r1.headers['Location'], allow_redirects=False)
    assert r2.status_code == 200
    assert "answer from port 82\n" in r2.text

def test_web3_has_custom_http_port_and_default_https_port(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://web3.nginx-proxy.tld:8080/port", allow_redirects=False)
    assert r1.status_code == 301
    assert r1.headers['Location'] == 'https://web3.nginx-proxy.tld/port'

    r2 = nginxproxy.get(r1.headers['Location'], allow_redirects=False)
    assert r2.status_code == 200
    assert "answer from port 83\n" in r2.text

def test_web4_has_default_http_and_https_ports(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://web4.nginx-proxy.tld/port", allow_redirects=False)
    assert r1.status_code == 301
    assert r1.headers['Location'] == 'https://web4.nginx-proxy.tld/port'

    r2 = nginxproxy.get(r1.headers['Location'], allow_redirects=False)
    assert r2.status_code == 200
    assert "answer from port 84\n" in r2.text
