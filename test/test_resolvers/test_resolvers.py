import docker

docker_client = docker.from_env()


def _generated_config(container_name: str) -> str:
    sut_container = docker_client.containers.get(container_name)
    assert sut_container.status == "running"
    exit_code, output = sut_container.exec_run("cat /etc/nginx/conf.d/default.conf")
    assert exit_code == 0, output.decode()
    return output.decode()


# Regression test for https://github.com/nginx-proxy/nginx-proxy/issues/2699:
# a user-provided RESOLVERS value must be honored and not overwritten by the
# entrypoint's autodetection from /etc/resolv.conf.
def test_user_provided_resolvers_is_honored(docker_compose):
    config = _generated_config("resolvers-custom")
    assert "resolver 8.8.8.8;" in config


# When RESOLVERS is not set, the entrypoint should still autodetect the resolvers
# from /etc/resolv.conf (Docker's embedded DNS on a user-defined network).
def test_resolvers_are_autodetected_when_unset(docker_compose):
    config = _generated_config("resolvers-auto")
    assert "resolver 127.0.0.11;" in config
