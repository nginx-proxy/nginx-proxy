import pytest

def test_custom_conf_does_not_apply_to_unknown_vhost(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/", allow_redirects=False)
    assert r.status_code == 503
    assert "X-test" not in r.headers

def test_custom_conf_applies_to_web2(docker_compose, nginxproxy):
    url = "web2.nginx-proxy.tld/port"
    r = nginxproxy.get(f"http://{url}", allow_redirects=False)
    assert r.status_code == 301
    assert "301 Moved Permanently" in r.text
    assert "X-test" in r.headers
    assert "f00" == r.headers["X-test"]
    assert "Location" in r.headers
    assert f"https://{url}" == r.headers["Location"]

def test_custom_conf_does_not_apply_to_web3(docker_compose, nginxproxy):
    url = "web3.nginx-proxy.tld/port"
    r = nginxproxy.get(f"http://{url}", allow_redirects=False)
    assert r.status_code == 301
    assert "301 Moved Permanently" in r.text
    assert "X-test" not in r.headers
    assert "Location" in r.headers
    assert f"https://{url}" == r.headers["Location"]

def test_custom_block_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    assert b"include /etc/nginx/vhost.d/web2.nginx-proxy.tld_location;" in nginxproxy.get_conf()
