import re


def test_answer_is_served_from_port_80_by_default(docker_compose, nginxproxy):
    r = nginxproxy.get("http://default-80.nginx-proxy.tld/port")
    assert r.status_code == 200
    if r.status_code == 200:
        assert "answer from port 80\n" in r.text

def test_answer_is_served_from_exposed_port_even_if_not_80(docker_compose, nginxproxy):
    r = nginxproxy.get("http://default-exposed.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text

def test_answer_is_served_from_chosen_port(docker_compose, nginxproxy):
    r = nginxproxy.get("http://virtual-port.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 90\n" in r.text

def test_answer_is_served_from_chosen_port_even_if_unreachable(docker_compose, nginxproxy):
    r = nginxproxy.get("http://wrong-virtual-port.nginx-proxy.tld/port", expected_status_code=502)
    assert r.status_code == 502
    assert re.search(r"\n\s+server \d+\.\d+\.\d+\.\d+:91;\n", nginxproxy.get_conf().decode('ASCII'))
