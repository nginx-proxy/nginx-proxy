from helpers import assert_ocsp_disabled, assert_ocsp_enabled


def test_ocsp_stapling_proxy_enabled_default_vhost(docker_compose, nginxproxy):
    host = "ocsp-proxy-enabled-default.nginx-proxy.tld"
    r = nginxproxy.get(f"http://{host}")
    assert r.status_code == 200

    conf = nginxproxy.get_conf().decode("ASCII")
    assert_ocsp_enabled(conf, host)


def test_ocsp_stapling_proxy_enabled_vhost_disabled(docker_compose, nginxproxy):
    host = "ocsp-proxy-enabled-vhost-disabled.nginx-proxy.tld"
    r = nginxproxy.get(f"http://{host}")
    assert r.status_code == 200

    conf = nginxproxy.get_conf().decode("ASCII")
    assert_ocsp_disabled(conf, host)
