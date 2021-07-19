import pytest
import re

def test_debug_info_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert re.search(r"# Exposed ports: \[\{\d+\.\d+\.\d+\.\d+\s+80\s+tcp \} \{\d+\.\d+\.\d+\.\d+\s+81\s+tcp \}\]", conf) or \
           re.search(r"# Exposed ports: \[\{\d+\.\d+\.\d+\.\d+\s+81\s+tcp \} \{\d+\.\d+\.\d+\.\d+\s+80\s+tcp \}\]", conf)
    assert conf.count("# Exposed ports: [{") == 1
