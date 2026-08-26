def test_forwards_to_container_joining_another_network_namespace_on_default_port(docker_compose, nginxproxy):
    r = nginxproxy.get("http://netns-joiner-default-port.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 80\n"

def test_forwards_to_container_joining_another_network_namespace_on_custom_port(docker_compose, nginxproxy):
    r = nginxproxy.get("http://netns-joiner-custom-port.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert r.text == "answer from port 8080\n"
