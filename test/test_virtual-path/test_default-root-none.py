import re
import time


def test_default_root_none(docker_compose, nginxproxy):
  time.sleep(3)
  conf = nginxproxy.get_conf().decode()
  assert re.search(r"(?m)^\s*location\s+/path\s+\{", conf)
  assert not re.search(r"(?m)^\s*location\s+/\s+\{", conf)

