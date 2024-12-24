def test_htpasswd_regex_virtual_host_is_restricted(docker_compose, nginxproxy):
    r = nginxproxy.get("http://regex.htpasswd.nginx-proxy.example/port")
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
    assert r.headers["WWW-Authenticate"] == 'Basic realm="Restricted access"'


def test_htpasswd_regex_virtual_host_basic_auth(docker_compose, nginxproxy):
    r = nginxproxy.get("http://regex.htpasswd.nginx-proxy.example/port", auth=("vhost", "password"))
    assert r.status_code == 200
    assert r.text == "answer from port 80\n"
