def test_custom_conf_applies_to_web1_by_stream(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.example:8000/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"
