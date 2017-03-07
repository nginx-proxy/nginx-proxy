import pytest
import os
import docker
import time
import subprocess
import re

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

def test_dhparam_is_not_generated_if_present(docker_compose, nginxproxy):
    wait_for_nginxproxy_to_be_ready()

    containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        assert 0
        return

    sut_container = containers[0]

    docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)

    assert "Custom dhparam.pem file found, generation skipped" in docker_logs

    # Make sure the dhparam in use is not the default, pre-generated one
    default_checksum = sut_container.exec_run("md5sum /app/dhparam.pem.default").split()
    current_checksum = sut_container.exec_run("md5sum /etc/nginx/dhparam/dhparam.pem").split()
    assert default_checksum[0] != current_checksum[0]

def test_web5_https_works(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web5.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 85\n" in r.text

def versiontuple(v):
    clean_v = re.sub("[^\d\.]", "", v)
    return tuple(map(int, (clean_v.split("."))))


# This code checks that the required version of OpenSSL is present, and skips the test if not
openssl_version_required = "1.0.2"
openssl_version = "0.0.0"

try:
    openssl_version = subprocess.check_output(["openssl", "version"]).split()[1]
except:
    pass

@pytest.mark.skipif(versiontuple(openssl_version) < versiontuple(openssl_version_required),
    reason="openssl command is not available in test environment or is less than version %s" % openssl_version_required)

def test_web5_dhparam_is_used(docker_compose, nginxproxy):
    containers = docker_client.containers.list(filters={"ancestor": "jwilder/nginx-proxy:test"})
    if len(containers) != 1:
        assert 0
        return

    sut_container = containers[0]

    host = "%s:443" % sut_container.attrs["NetworkSettings"]["IPAddress"]
    r = subprocess.check_output("echo '' | openssl s_client -verify 0 -connect %s -cipher 'EDH' | grep 'Server Temp Key'" % host, shell=True)
    assert "Server Temp Key: DH, 2048 bits" in r
