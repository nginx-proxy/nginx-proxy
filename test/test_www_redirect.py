import pytest

# HTTP
# Testing a webapp which just serves via http (no https and no https-redirect)
def test_non_www_http_not_redirected(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 200

def test_www_http_redirected(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.web.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "http://web.nginx-proxy.tld/" == r.headers['Location']

def test_www_http_redirected_uri(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.web.nginx-proxy.tld/mysite.php", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "http://web.nginx-proxy.tld/mysite.php" == r.headers['Location']

# HTTPS
# Testing a webapp which serves via http and https (https redirect activated)
def test_non_www_https_not_redirected(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web2.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 200

def test_www_https_redirected(docker_compose, nginxproxy):
    r = nginxproxy.get("https://www.web2.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://web2.nginx-proxy.tld/" == r.headers['Location']

def test_www_https_redirected_uri(docker_compose, nginxproxy):
    r = nginxproxy.get("https://www.web2.nginx-proxy.tld/mysite.php", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://web2.nginx-proxy.tld/mysite.php" == r.headers['Location']

def test_www_http_redirected_nonwww_https(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.web2.nginx-proxy.tld/", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://web2.nginx-proxy.tld/" == r.headers['Location']

def test_www_http_redirected_nonwww_https_uri(docker_compose, nginxproxy):
    r = nginxproxy.get("http://www.web2.nginx-proxy.tld/mysite.php", allow_redirects=False)
    assert r.status_code == 301
    assert "Location" in r.headers
    assert "https://web2.nginx-proxy.tld/mysite.php" == r.headers['Location']