import socket


def test_proxy_protocol_global_disabled_X_Forwarded_For_is_generated(
    docker_compose, nginxproxy
):
    r = nginxproxy.get("http://proxy-protocol-global-disabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-For:" in r.text


def test_proxy_protocol_global_disabled_X_Forwarded_For_is_passed_on(
    docker_compose, nginxproxy
):
    r = nginxproxy.get(
        "http://proxy-protocol-global-disabled.nginx-proxy.tld/headers",
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    assert r.status_code == 200
    assert "X-Forwarded-For: 1.2.3.4, " in r.text


def test_proxy_protocol_global_disabled_X_Forwarded_Port_is_generated(
    docker_compose, nginxproxy
):
    r = nginxproxy.get("http://proxy-protocol-global-disabled.nginx-proxy.tld/headers")
    assert r.status_code == 200
    assert "X-Forwarded-Port: 80\n" in r.text


def test_proxy_protocol_global_disabled_X_Forwarded_Port_is_passed_on(
    docker_compose, nginxproxy
):
    r = nginxproxy.get(
        "http://proxy-protocol-global-disabled.nginx-proxy.tld/headers",
        headers={"X-Forwarded-Port": "1234"},
    )
    assert r.status_code == 200
    assert "X-Forwarded-Port: 1234\n" in r.text


def test_proxy_protocol_global_disabled_proto_request_fails(docker_compose, nginxproxy):
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
    assert "HTTP/1.1 400 Bad Request" in response
