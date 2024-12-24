def test_explicit_root_nohash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://explicit-root-nohash.nginx-proxy.test/port")
    assert r.status_code == 418
    r = nginxproxy.get("http://explicit-root-nohash.nginx-proxy.test/foo/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n"

def test_explicit_root_hash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://explicit-root-hash.nginx-proxy.test/port")
    assert r.status_code == 418
    r = nginxproxy.get("http://explicit-root-hash.nginx-proxy.test/foo/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n"

def test_explicit_root_hash_and_nohash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://explicit-root-hash-and-nohash.nginx-proxy.test/port")
    assert r.status_code == 418
    r = nginxproxy.get("http://explicit-root-hash-and-nohash.nginx-proxy.test/foo/port")
    assert r.status_code == 200
    assert r.text == "answer from port 82\n"

def test_explicit_nonroot(docker_compose, nginxproxy):
    r = nginxproxy.get("http://explicit-nonroot.nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"
    r = nginxproxy.get("http://explicit-nonroot.nginx-proxy.test/foo/port")
    assert r.status_code == 418

def test_implicit_root_nohash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://implicit-root-nohash.nginx-proxy.test/port")
    assert r.status_code == 418

def test_implicit_root_hash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://implicit-root-hash.nginx-proxy.test/port")
    assert r.status_code == 418

def test_implicit_root_hash_and_nohash(docker_compose, nginxproxy):
    r = nginxproxy.get("http://implicit-root-hash-and-nohash.nginx-proxy.test/port")
    assert r.status_code == 418
