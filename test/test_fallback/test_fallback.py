import pathlib
import re
from typing import List, Callable

import backoff
import pytest
import requests
from requests import Response


@pytest.fixture
def docker_compose_files(compose_file) -> List[str]:
    data_dir = pathlib.Path(__file__).parent.joinpath("test_fallback.data")
    return [
        data_dir.joinpath("compose.base.yml"),
        data_dir.joinpath(compose_file).as_posix()
    ]


@pytest.fixture
def get(docker_compose, nginxproxy, want_err_re: re.Pattern[str]) -> Callable[[str], Response]:
    @backoff.on_exception(
        backoff.constant,
        requests.exceptions.SSLError,
        giveup=lambda e: want_err_re and bool(want_err_re.search(str(e))),
        interval=.3,
        max_tries=30,
        jitter=None)
    def _get(url) -> Response:
        return nginxproxy.get(url, allow_redirects=False)

    return _get


INTERNAL_ERR_RE = re.compile("TLSV1_UNRECOGNIZED_NAME")


@pytest.mark.parametrize("compose_file,url,want_code,want_err_re", [
    # Has default.crt.
    ("withdefault.yml", "http://https-and-http.nginx-proxy.test/", 301, None),
    ("withdefault.yml", "https://https-and-http.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "https://http-only.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "http://missing-cert.nginx-proxy.test/", 301, None),
    ("withdefault.yml", "https://missing-cert.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "http://missing-cert.default-untrusted.nginx-proxy.test/", 200, None),
    ("withdefault.yml", "https://missing-cert.default-untrusted.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("withdefault.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("withdefault.yml", "https://unknown.nginx-proxy.test/", 503, None),
    # Same as withdefault.yml, except default.crt is not trusted (TRUST_DEFAULT_CERT=false).
    ("untrusteddefault.yml", "http://https-and-http.nginx-proxy.test/", 301, None),
    ("untrusteddefault.yml", "https://https-and-http.nginx-proxy.test/", 200, None),
    ("untrusteddefault.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("untrusteddefault.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("untrusteddefault.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("untrusteddefault.yml", "https://http-only.nginx-proxy.test/", 503, None),
    ("untrusteddefault.yml", "http://missing-cert.nginx-proxy.test/", 200, None),
    ("untrusteddefault.yml", "https://missing-cert.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("untrusteddefault.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("untrusteddefault.yml", "https://unknown.nginx-proxy.test/", 503, None),
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
    # HTTPS_METHOD=nohttp on nginx-proxy, HTTPS_METHOD unset on the app container.
    ("nohttp.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("nohttp.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("nohttp.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nohttp.yml", "https://unknown.nginx-proxy.test/", 503, None),
    # HTTPS_METHOD=redirect on nginx-proxy, HTTPS_METHOD=nohttp on the app container.
    ("nohttp-on-app.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("nohttp-on-app.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("nohttp-on-app.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nohttp-on-app.yml", "https://unknown.nginx-proxy.test/", 503, None),
    # Same as nohttp.yml, except there are two vhosts with a missing cert, the second
    # one being configured not to trust the default certificate. This causes its
    # HTTPS_METHOD=nohttp setting to effectively become HTTPS_METHOD=noredirect.
    ("nohttp-with-missing-cert.yml", "http://https-only.nginx-proxy.test/", 503, None),
    ("nohttp-with-missing-cert.yml", "https://https-only.nginx-proxy.test/", 200, None),
    ("nohttp-with-missing-cert.yml", "http://missing-cert.nginx-proxy.test/", 503, None),
    ("nohttp-with-missing-cert.yml", "https://missing-cert.nginx-proxy.test/", 200, None),
    ("nohttp-with-missing-cert.yml", "http://missing-cert.default-untrusted.nginx-proxy.test/", 200, None),
    ("nohttp-with-missing-cert.yml", "https://missing-cert.default-untrusted.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("nohttp-with-missing-cert.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nohttp-with-missing-cert.yml", "https://unknown.nginx-proxy.test/", 503, None),
    # HTTPS_METHOD=nohttps on nginx-proxy, HTTPS_METHOD unset on the app container.
    ("nohttps.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("nohttps.yml", "https://http-only.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("nohttps.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nohttps.yml", "https://unknown.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    # HTTPS_METHOD=redirect on nginx-proxy, HTTPS_METHOD=nohttps on the app container.
    ("nohttps-on-app.yml", "http://http-only.nginx-proxy.test/", 200, None),
    ("nohttps-on-app.yml", "https://http-only.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    ("nohttps-on-app.yml", "http://unknown.nginx-proxy.test/", 503, None),
    ("nohttps-on-app.yml", "https://unknown.nginx-proxy.test/", None, INTERNAL_ERR_RE),
    # Custom nginx config that has a `server` directive that uses `default_server` and simply
    # returns 418.  Nginx should successfully start (in particular, the `default_server` in the
    # custom config should not conflict with the fallback server generated by nginx-proxy) and nginx
    # should prefer that server for handling requests for unknown vhosts.
    ("custom-fallback.yml", "http://unknown.nginx-proxy.test/", 418, None),
])
def test_fallback(get, compose_file, url, want_code, want_err_re):
    if want_err_re is None:
        r = get(url)
        assert r.status_code == want_code
    else:
        with pytest.raises(requests.exceptions.SSLError, match=want_err_re):
            get(url)
