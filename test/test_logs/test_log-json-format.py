import time


def get_docker_logs(container, match, timeout=5):
    # Fork: nginx.conf buffers the access log (buffer=64k flush=1s), wait for the flush.
    deadline = time.time() + timeout
    while True:
        docker_logs = container.logs(stdout=True, stderr=True, stream=False, follow=False)
        docker_logs = [line for line in docker_logs.decode("utf-8").splitlines() if match in line]
        if docker_logs or time.time() > deadline:
            return docker_logs
        time.sleep(0.5)


def test_log_json_format(docker_compose, nginxproxy):
    log_conf = [line for line in nginxproxy.get_conf().decode('ASCII').splitlines() if "log_format vhost escape=" in line]
    assert "{\"time_local\":\"$time_iso8601\"," in log_conf[0]

    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"
    sut_container = docker_compose.containers.get("nginx-proxy")
    docker_logs = get_docker_logs(sut_container, "{\"time_local\":")
    assert "GET /port" in docker_logs[0]
