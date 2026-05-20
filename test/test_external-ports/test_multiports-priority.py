def test_multiports_external_port_takes_precedence_over_virtualhost_external_port(docker_compose, nginxproxy):
    r1 = nginxproxy.get("http://shared.nginx-proxy.tld/multiports/port", allow_redirects=False)
    assert r1.status_code == 301
    assert r1.headers['Location'] == 'https://shared.nginx-proxy.tld:9443/multiports/port'

    r2 = nginxproxy.get(r1.headers['Location'], allow_redirects=False)
    assert r2.status_code == 200
    assert "answer from port 81\n" in r2.text

    r3 = nginxproxy.get("http://shared.nginx-proxy.tld/virtualhost/port", allow_redirects=False)
    assert r3.status_code == 301
    assert r3.headers['Location'] == 'https://shared.nginx-proxy.tld:9443/virtualhost/port'

    r4 = nginxproxy.get(r3.headers['Location'], allow_redirects=False)
    assert r4.status_code == 200
    assert "answer from port 82\n" in r4.text
