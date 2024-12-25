import re
import time


def test_answer_is_served_from_virtual_port_which_is_ureachable(docker_compose, nginxproxy):
    time.sleep(3)
    r = nginxproxy.get("http://web.nginx-proxy.tld/port", expected_status_code=502)
    assert r.status_code == 502
    assert re.search(r"\n\s+server \d+\.\d+\.\d+\.\d+:90;\n", nginxproxy.get_conf().decode('ASCII'))
