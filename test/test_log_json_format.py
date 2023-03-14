import pytest

def test_log_json_format(docker_compose, nginxproxy):
    log_conf = [line for line in nginxproxy.get_conf().decode('ASCII').splitlines() if "log_format vhost escape=" in line]
    assert "{\"time_local\":\"$time_iso8601\"," in log_conf[0]

    r = nginxproxy.get("http://nginx-proxy.test/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"
    sut_container = docker_compose.containers.get("sut")
    docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)
    docker_logs = docker_logs.decode("utf-8").splitlines()
    docker_logs = [line for line in docker_logs if "{\"time_local\":" in line]
    assert "GET /port" in docker_logs[0]


