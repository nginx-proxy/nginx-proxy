from time import sleep

import pytest
import re
import docker


docker_client = docker.from_env()
RE_PGREP_RESPONSE = re.compile("^(?P<pid>\d+)\n", re.MULTILINE)


def get_pid(process_name):
    pgrep_response = docker_client.containers.get("nginx-proxy").exec_run("pgrep %s" % process_name)
    pids = []
    for m in RE_PGREP_RESPONSE.finditer(pgrep_response):
        pids.append(int(m.group("pid")))
    assert len(pids) > 0
    return set(pids)


def kill(process_name):
    docker_client.containers.get("nginx-proxy").exec_run("pkill %s" % process_name)
    sleep(2)


def assert_reverse_proxy_behavior(nginxproxy):
    assert "answer from port 81\n" == nginxproxy.get("http://web1.nginx-proxy/port").text
    docker_client.containers.get("web1").stop()
    sleep(2)
    assert nginxproxy.get("http://web1.nginx-proxy/").status_code == 503
    docker_client.containers.get("web1").start()
    sleep(2)
    assert "answer from port 81\n" == nginxproxy.get("http://web1.nginx-proxy/port").text


###############################################################################

def test_dockergen_is_restarted_when_killed(docker_compose, nginxproxy):
    assert_reverse_proxy_behavior(nginxproxy)
    first_pids = get_pid("docker-gen")
    kill("docker-gen")
    assert_reverse_proxy_behavior(nginxproxy)
    second_pids = get_pid("docker-gen")
    assert first_pids != second_pids


def test_nginx_is_restarted_when_killed(docker_compose, nginxproxy):
    assert_reverse_proxy_behavior(nginxproxy)
    first_pids = get_pid("nginx")
    kill("nginx")
    assert_reverse_proxy_behavior(nginxproxy)
    second_pids = get_pid("nginx")
    assert len(first_pids.intersection(second_pids)) == 0


def test_term_signal_exits_nginxproxy(docker_compose):
    assert "running" == docker_compose.containers.get("nginx-proxy").status
    print docker_compose.containers.get("nginx-proxy").exec_run("kill -TERM 1")
    sleep(2)
    assert "exited" == docker_compose.containers.get("nginx-proxy").status
