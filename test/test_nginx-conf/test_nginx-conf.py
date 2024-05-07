import pytest
import re


def test_nginx_toplevel_conf_contains_customizations(docker_compose, nginxproxy):
    conf = nginxproxy.get_toplevel_conf().decode('ASCII')
    assert re.search(r"^ +worker_connections  10240;$", conf)
    assert re.search(r"^worker_rlimit_nofile 20480;$", conf)
