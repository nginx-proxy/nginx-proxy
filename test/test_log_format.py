import pytest

def test_log_format(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"
    sut_container = docker_compose.containers.get("sut")
    docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)
    docker_logs = docker_logs.decode("utf-8").splitlines()
    docker_logs = [line for line in docker_logs if "GET /port" in line]
    assert "request_time=" in docker_logs[0]
