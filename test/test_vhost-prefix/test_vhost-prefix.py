def test_web1_vhost_prefix(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.tld:80/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 80\n" in r.text


def test_web1_other_vhost_prefix_no_answer(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web2.nginx-proxy.tld:80/port", allow_redirects=False)
    assert r.status_code == 503

