import re

import pytest


@pytest.mark.parametrize('url,header,input,want', [
    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Proto', None, 'http'),
    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Proto', 'f00', 'f00'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Proto', None, 'https'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Proto', 'f00', 'f00'),

    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Host', None, 'web.nginx-proxy.tld'),
    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Host', 'example.com', 'example.com'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Host', None, 'web.nginx-proxy.tld'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Host', 'example.com', 'example.com'),

    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Port', None, '80'),
    ('http://web.nginx-proxy.tld/headers', 'X-Forwarded-Port', '1234', '1234'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Port', None, '443'),
    ('https://web.nginx-proxy.tld/headers', 'X-Forwarded-Port', '1234', '1234'),
])
def test_downstream_proxy_header(docker_compose, nginxproxy, url, header, input, want):
    kwargs = {} if input is None else {'headers': {header: input}}
    r = nginxproxy.get(url, **kwargs)
    assert r.status_code == 200
    assert re.search(fr'(?m)^(?i:{re.escape(header)}): {re.escape(want)}$', r.text)
