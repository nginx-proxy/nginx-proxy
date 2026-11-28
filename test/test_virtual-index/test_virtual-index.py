import re


def _server_block(conf: str, server_name: str) -> str:
    """Return the text of the server { } block whose server_name matches."""
    idx = conf.index(f"server_name {server_name};")
    start = conf.rindex("server {", 0, idx)
    depth = 0
    for i in range(start, len(conf)):
        if conf[i] == "{":
            depth += 1
        elif conf[i] == "}":
            depth -= 1
            if depth == 0:
                return conf[start:i + 1]
    return conf[start:]


def test_virtual_index_directive_present_when_set(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode("ASCII")
    block = _server_block(conf, "index-set.nginx-proxy.tld")
    assert "index index.php;" in block


def test_virtual_index_directive_absent_when_unset(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode("ASCII")
    block = _server_block(conf, "index-unset.nginx-proxy.tld")
    # No bare `index` directive should be emitted (avoid matching `fastcgi_index`, etc.)
    assert re.search(r"^\s*index\s", block, re.MULTILINE) is None
