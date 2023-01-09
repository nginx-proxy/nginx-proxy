import pytest


def test_port_80_is_server_by_location_root(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text

def test_port_81_is_server_by_location_slash81(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/81/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text

def test_port_82_is_server_by_location_slash82_with_dest_slashport(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/82")
    assert r.status_code == 200
    assert "answer from port 82\n" in r.text

def test_port_83_is_server_by_regex_location_slash83_with_rewrite_in_custom_location_file(docker_compose, nginxproxy):
    # The custom location file with rewrite is requested because when
    # location is specified using a regex then proxy_pass should be
    # specified without a URI
    # see http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass
    r = nginxproxy.get("http://web.nginx-proxy.tld/83/port")
    assert r.status_code == 200
    assert "answer from port 83\n" in r.text
