import re


def test_default_root_none(docker_compose, nginxproxy):
  conf = nginxproxy.get_conf().decode()
  assert re.search(r"(?m)^\s*location\s+/path\s+\{", conf)
  assert not re.search(r"(?m)^\s*location\s+/\s+\{", conf)

