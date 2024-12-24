import pytest
import re
import time


def test_predictable_upstream_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    time.sleep(3)
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"upstream web\.nginx-proxy\.tld \{", conf)
