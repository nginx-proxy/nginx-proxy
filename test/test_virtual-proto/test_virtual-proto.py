import pytest


@pytest.mark.parametrize('subdomain', ['web1', 'web2', 'web3'])
def test_upstream_with_https_virtual_proto(docker_compose, nginxproxy, subdomain):
    r = nginxproxy.get(f"http://{subdomain}.nginx-proxy.tld")
    assert r.status_code == 200
    assert r.text == f"This is {subdomain}.nginx-proxy.tld"
