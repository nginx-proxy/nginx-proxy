def test_htpasswd_virtual_path_is_restricted(docker_compose, nginxproxy):
    r = nginxproxy.get("http://htpasswd.nginx-proxy.tld/foo/port", expected_status_code=401)
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
    assert r.headers["WWW-Authenticate"] == 'Basic realm="Restricted htpasswd.nginx-proxy.tld/foo/"'


def test_htpasswd_virtual_path_basic_auth(docker_compose, nginxproxy):
    r = nginxproxy.get("http://htpasswd.nginx-proxy.tld/foo/port", auth=("vpath", "password"))
    assert r.status_code == 200
    assert r.text == "answer from port 80\n"
