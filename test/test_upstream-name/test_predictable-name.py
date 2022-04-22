import pytest
import re


def test_predictable_upstream_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"upstream web\.nginx-proxy\.tld \{", conf)
