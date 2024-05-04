import pytest


def test_templatefile_was_rendered_by_nginx_entrypoint(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    assert "# some_directive FOOBARBAZ;" in conf
