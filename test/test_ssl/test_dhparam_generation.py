import backoff
import docker

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


###############################################################################
#
# Tests
#
###############################################################################

def test_dhparam_is_generated_if_missing(docker_compose):
    sut_container = docker_client.containers.get("nginxproxy")
    assert sut_container.status == "running"

    assert_log_contains("Generating DH parameters")
    assert_log_contains("dhparam generation complete, reloading nginx")

    # Make sure the dhparam in use is not the default, pre-generated one
    default_checksum = sut_container.exec_run("md5sum /app/dhparam.pem.default").split()
    generated_checksum = sut_container.exec_run("md5sum /etc/nginx/dhparam/dhparam.pem").split()
    assert default_checksum[0] != generated_checksum[0]
