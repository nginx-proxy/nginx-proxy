import pytest
import re


def test_virtual_hosts_with_syntax_error_should_not_be_reachable(docker_compose, nginxproxy):
    r = nginxproxy.get("http://test1.nginx-proxy.tld")
    assert r.status_code == 503
    r = nginxproxy.get("http://test2.nginx-proxy.tld")
    assert r.status_code == 503


def test_config_should_have_multiports_warning_comments(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    matches = re.findall(r"the VIRTUAL_HOST_MULTIPORTS environment variable used for this container is not a valid YAML string", conf)
    assert len(matches) == 3
    assert "# invalidsyntax" in conf
    assert "# hostnamerepeat" in conf
    assert "# pathrepeat" in conf
