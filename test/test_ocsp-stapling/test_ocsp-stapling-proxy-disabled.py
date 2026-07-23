from helpers import assert_ocsp_disabled, assert_ocsp_enabled


def test_ocsp_stapling_proxy_disabled_default_vhost(docker_compose, nginxproxy):
    host = "ocsp-proxy-disabled-default.nginx-proxy.tld"
    r = nginxproxy.get(f"http://{host}")
    assert r.status_code == 200

    conf = nginxproxy.get_conf().decode("ASCII")
    assert_ocsp_disabled(conf, host)


def test_ocsp_stapling_proxy_disabled_vhost_enabled(docker_compose, nginxproxy):
    host = "ocsp-proxy-disabled-vhost-enabled.nginx-proxy.tld"
    r = nginxproxy.get(f"http://{host}")
    assert r.status_code == 200

    conf = nginxproxy.get_conf().decode("ASCII")
    assert_ocsp_enabled(conf, host)
