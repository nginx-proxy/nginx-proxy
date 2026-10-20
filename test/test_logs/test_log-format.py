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


def test_log_format(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"
    sut_container = docker_compose.containers.get("nginx-proxy")
    docker_logs = get_docker_logs(sut_container, "GET /port")
    assert "request_time=" in docker_logs[0]
