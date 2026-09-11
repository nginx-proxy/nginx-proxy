def _server_blocks(conf: str, server_name: str) -> list:
    """Return every server { } block whose server_name matches.

    A vhost can produce more than one server block (e.g. an HTTP redirect
    server plus the main server), so all matching blocks are collected.
    """
    blocks = []
    needle = f"server_name {server_name};"
    pos = 0
    while True:
        idx = conf.find(needle, pos)
        if idx == -1:
            break
        start = conf.rindex("server {", 0, idx)
        depth = 0
        end = len(conf)
        for i in range(start, len(conf)):
            if conf[i] == "{":
                depth += 1
            elif conf[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        blocks.append(conf[start:end])
        pos = end
    return blocks


def test_x_robots_tag_header_present_when_set(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode("ASCII")
    blocks = _server_blocks(conf, "robots-set.nginx-proxy.tld")
    assert blocks, "no server block found for robots-set.nginx-proxy.tld"
    # The directive must be present in every server block of the vhost.
    assert all('add_header X-Robots-Tag "noindex, nofollow" always;' in b for b in blocks)


def test_x_robots_tag_header_absent_when_unset(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode("ASCII")
    blocks = _server_blocks(conf, "robots-unset.nginx-proxy.tld")
    assert blocks, "no server block found for robots-unset.nginx-proxy.tld"
    assert all("X-Robots-Tag" not in b for b in blocks)
