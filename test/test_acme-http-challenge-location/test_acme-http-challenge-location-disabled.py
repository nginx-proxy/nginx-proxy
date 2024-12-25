def test_redirect_acme_challenge_location_disabled(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web1.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False,
        expected_status_code=301
    )
    assert r.status_code == 301


def test_redirect_acme_challenge_location_enabled(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web2.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 200


def test_noredirect_acme_challenge_location_disabled(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web3.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False,
        expected_status_code=404
    )
    assert r.status_code == 404


def test_noredirect_acme_challenge_location_enabled(docker_compose, nginxproxy, acme_challenge_path):
    r = nginxproxy.get(
        f"http://web4.nginx-proxy.tld/{acme_challenge_path}",
        allow_redirects=False
    )
    assert r.status_code == 200
