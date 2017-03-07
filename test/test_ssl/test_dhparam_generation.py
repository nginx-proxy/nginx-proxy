import pytest
import os
import docker
import time

docker_client = docker.from_env()

def wait_for_nginxproxy_to_be_ready():
    """
    If one (and only one) container started from image jwilder/nginx-proxy:test is found,
    wait for its log to contain substring "Watching docker events"
    """
    containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        return
    container = containers[0]
    for line in container.logs(stream=True):
        if "Watching docker events" in line:
            break

def test_dhparam_is_generated_if_missing(docker_compose, nginxproxy):
    wait_for_nginxproxy_to_be_ready()

    containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        assert 0
        return

    sut_container = containers[0]

    docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)

    assert "Generating DH parameters" in docker_logs

    expected_line = "dhparam generation complete, reloading nginx"
    max_wait = 30
    sleep_interval = 2
    current_wait = 0

    while current_wait < max_wait:
        docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)
        if expected_line in docker_logs:
            break

        time.sleep(sleep_interval)
        current_wait += sleep_interval

    # Re-check the logs to get better assert output on failure
    assert expected_line in docker_logs

    # Make sure the dhparam in use is not the default, pre-generated one
    default_checksum = sut_container.exec_run("md5sum /app/dhparam.pem.default").split()
    generated_checksum = sut_container.exec_run("md5sum /etc/nginx/dhparam/dhparam.pem").split()
    assert default_checksum[0] != generated_checksum[0]
