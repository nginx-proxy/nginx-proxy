import pytest


# Marked flaky: this test depends on the proxied vhost being generated and reloaded
# before the request, which can race with container startup under CI load (observed
# returning 404 before the upstream was ready). See pytest-ignore-flaky.
@pytest.mark.flaky
def test_web_has_no_server_down(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode('ASCII')
    r = nginxproxy.get("http://web.nginx-proxy.tld/port")
    assert r.status_code == 200
    assert (r.text == "answer from port 81\n") or (r.text == "answer from port 82\n")
    assert conf.count("server 127.0.0.1 down;") == 0
