import pytest

def test_custom_conf_does_not_apply_to_unknown_vpath(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.local/")
    assert r.status_code == 503
    assert "X-test" not in r.headers

def test_custom_conf_applies_to_path1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.local/path1/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 81\n"
    assert "X-test" in r.headers
    assert "f00" == r.headers["X-test"]

def test_custom_conf_does_not_apply_to_path2(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.local/path2/port")
    assert r.status_code == 200   
    assert r.text == "answer from port 82\n"
    assert "X-test" not in r.headers

def test_custom_block_is_present_in_nginx_generated_conf(docker_compose, nginxproxy):
    assert b"include /etc/nginx/vhost.d/nginx-proxy.local_faeee25c67f4f2196a5cf9c7b87b970ed63140de_location;" in nginxproxy.get_conf()
