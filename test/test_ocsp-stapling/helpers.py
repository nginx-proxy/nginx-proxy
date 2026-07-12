import re


def _vhost_has_directive(conf, host, directive):
    return re.search(
        rf"server_name {re.escape(host)};(?:(?!server_name ).)*{directive}",
        conf,
        re.S,
    ) is not None


def assert_ocsp_enabled(conf, host):
    assert _vhost_has_directive(conf, host, r"ssl_stapling on;")
    assert _vhost_has_directive(conf, host, r"ssl_stapling_verify on;")
    assert _vhost_has_directive(
        conf,
        host,
        r"ssl_trusted_certificate /etc/nginx/certs/nginx-proxy\.tld\.chain\.pem;",
    )


def assert_ocsp_disabled(conf, host):
    assert not _vhost_has_directive(conf, host, r"ssl_stapling on;")
    assert not _vhost_has_directive(conf, host, r"ssl_stapling_verify on;")
    assert not _vhost_has_directive(
        conf,
        host,
        r"ssl_trusted_certificate /etc/nginx/certs/nginx-proxy\.tld\.chain\.pem;",
    )
