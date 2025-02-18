import socket


def test_proxy_protocol_global_enabled_normal_request_fails(docker_compose, nginxproxy):
    try:
        r = nginxproxy.get(
            "http://proxy-protocol-global-enabled.nginx-proxy.tld/headers"
        )
        assert False
    except Exception as e:
        assert "Remote end closed connection without response" in str(e)


def test_proxy_protocol_global_enabled_proto_request_works(docker_compose, nginxproxy):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((nginxproxy.get_ip(), 80))

    # 1.2.3.4 is the client IP
    # 4.3.2.1 is the proxy server IP
    # 8080 is the client port
    # 9090 is the proxy server port
    client.send(f"PROXY TCP4 1.2.3.4 4.3.2.1 8080 9090\r\n".encode("utf-8"))
    client.send(
        "GET /headers HTTP/1.1\r\nHost: proxy-protocol-global-enabled.nginx-proxy.tld\r\n\r\n".encode(
            "utf-8"
        )
    )

    response = client.recv(4096).decode("utf-8")
    assert "X-Forwarded-For: 1.2.3.4" in response
    assert "X-Forwarded-Port: 9090" in response
