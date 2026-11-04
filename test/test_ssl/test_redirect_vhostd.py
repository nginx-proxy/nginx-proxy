def test_vhostd_files_included_in_redirect_server_block(docker_compose, nginxproxy):
    conf = nginxproxy.get_conf().decode("ASCII")
    # With a certificate present, nginx-proxy.tld gets an https_method=redirect server
    # block in addition to the main server block. The server-level vhost.d include must
    # now appear in BOTH (it previously appeared only in the main block).
    assert conf.count("include /etc/nginx/vhost.d/nginx-proxy.tld;") == 2
    # Likewise the per-vhost location include must appear in both the redirect `location /`
    # and the main `location /`.
    assert conf.count("include /etc/nginx/vhost.d/nginx-proxy.tld_location;") == 2
