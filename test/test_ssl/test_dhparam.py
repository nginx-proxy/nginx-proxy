import re
import subprocess

import backoff
import docker
import pytest

docker_client = docker.from_env()


###############################################################################
#
# Tests helpers
#
###############################################################################

@backoff.on_exception(backoff.constant, AssertionError, interval=2, max_tries=15, jitter=None)
def assert_log_contains(expected_log_line):
    """
    Check that the nginx-proxy container log contains a given string.
    The backoff decorator will retry the check 15 times with a 2 seconds delay.

    :param expected_log_line: string to search for
    :return: None
    :raises: AssertError if the expected string is not found in the log
    """
    sut_container = docker_client.containers.get("nginxproxy")
    docker_logs = sut_container.logs(stdout=True, stderr=True, stream=False, follow=False)
    assert expected_log_line in docker_logs


def require_openssl(required_version):
    """
    This function checks that the required version of OpenSSL is present, and skips the test if not.
    Use it as a test function decorator:

        @require_openssl("2.3.4")
        def test_something():
            ...

    :param required_version: minimal required version as a string: "1.2.3"
    """

    def versiontuple(v):
        clean_v = re.sub("[^\d\.]", "", v)
        return tuple(map(int, (clean_v.split("."))))

    try:
        command_output = subprocess.check_output(["openssl", "version"])
    except OSError:
        return pytest.mark.skip("openssl command is not available in test environment")
    else:
        if not command_output:
            raise Exception("Could not get openssl version")
        openssl_version = command_output.split()[1]
        return pytest.mark.skipif(
            versiontuple(openssl_version) < versiontuple(required_version),
            reason="openssl v%s is less than required version %s" % (openssl_version, required_version))


###############################################################################
#
# Tests
#
###############################################################################

def test_dhparam_is_not_generated_if_present(docker_compose):
    sut_container = docker_client.containers.get("nginxproxy")
    assert sut_container.status == "running"

    assert_log_contains("Custom dhparam.pem file found, generation skipped")

    # Make sure the dhparam in use is not the default, pre-generated one
    default_checksum = sut_container.exec_run("md5sum /app/dhparam.pem.default").split()
    current_checksum = sut_container.exec_run("md5sum /etc/nginx/dhparam/dhparam.pem").split()
    assert default_checksum[0] != current_checksum[0]


def test_web5_https_works(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web5.nginx-proxy.tld/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 85\n" in r.text


@require_openssl("1.0.2")
def test_web5_dhparam_is_used(docker_compose):
    sut_container = docker_client.containers.get("nginxproxy")
    assert sut_container.status == "running"

    host = "%s:443" % sut_container.attrs["NetworkSettings"]["IPAddress"]
    r = subprocess.check_output(
        "echo '' | openssl s_client -connect %s -cipher 'EDH' | grep 'Server Temp Key'" % host, shell=True)
    assert "Server Temp Key: X25519, 253 bits\n" == r
