def test_answer_is_served_when_virtual_port_has_whitespace(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 90\n" in r.text
