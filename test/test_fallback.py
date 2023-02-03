import os.path
import re

import backoff
import pytest
import requests


@pytest.fixture
def data_dir():
    return f"{os.path.splitext(__file__)[0]}.data"


@pytest.fixture
def docker_compose_file(data_dir, compose_file):
    return os.path.join(data_dir, compose_file)


@pytest.fixture
def get(docker_compose, nginxproxy, want_err_re):

    @backoff.on_exception(
        backoff.constant,
        requests.exceptions.RequestException,
        giveup=lambda e: want_err_re and want_err_re.search(str(e)),
        interval=.3,
        max_tries=30,
        jitter=None)
    def _get(url):
        return nginxproxy.get(url, allow_redirects=False)

    return _get


INTERNAL_ERR_RE = re.compile("TLSV1_ALERT_INTERNAL_ERROR")


@pytest.mark.parametrize("compose_file,url,want_code,want_err_re", [
    # Has default.crt.
    ("withdefault.yml", "http://https-and-http.nginx-proxy.test/", 301, None),
    ("withdefault.yml", "https://https-and-http.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "https://http-only.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "http://missing-cert.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "https://missing-cert.nginx-proxy.test/", 500, None),
    ("withdefault.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "https://unknown.nginx-proxy.test/", 503, None),
    # Same as withdefault.yml, except there is no default.crt.
    ("nodefault.yml", "http://https-and-http.nginx-proxy.test/", 301, None),
    ("nodefault.yml", "https://https-and-http.nginx-proxy.test/", 200, None),
    ("nodefault.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("nodefault.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("nodefault.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("nodefault.yml", "https://http-only.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("nodefault.yml", "http://missing-cert.nginx-proxy.test/", 200, None),
    ("nodefault.yml", "https://missing-cert.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("nodefault.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nodefault.yml", "https://unknown.nginx-proxy.test/", None, INTERNAL_ERR_RE),
])
def test_fallback(get, url, want_code, want_err_re):
    if want_err_re is None:
        r = get(url)
        assert r.status_code == want_code
    else:
        with pytest.raises(requests.exceptions.RequestException, match=want_err_re):
            get(url)
