import pytest
import time


def test_dockergen_is_running(docker_compose):
    assert docker_compose.containers.get("reverseproxy").exec_run("pgrep docker-gen") != ''


def test_nginx_is_running(docker_compose):
    assert docker_compose.containers.get("reverseproxy").exec_run("pgrep nginx") != ''


def test_nginx_answers_with_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503


def test_survive_restart(docker_compose, nginxproxy):
    docker_compose.containers.get("reverseproxy").restart()
    time.sleep(2)  # give time to eventually fail
    assert docker_compose.containers.get("reverseproxy").status == "running"


def test_dockergen_is_still_running(docker_compose):
    assert docker_compose.containers.get("reverseproxy").exec_run("pgrep -c docker-gen") != ''


def test_nginx_is_still_running(docker_compose):
    assert docker_compose.containers.get("reverseproxy").exec_run("pgrep -c nginx") != ''


def test_nginx_still_answers_with_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://nginx-proxy/")
    assert r.status_code == 503
