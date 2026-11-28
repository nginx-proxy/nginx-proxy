"""
Regression test for https://github.com/nginx-proxy/nginx-proxy/issues/1238:
the entrypoint/CMD must not depend on WORKDIR being set to /app. When a
downstream image overrides WORKDIR, forego used to look for the Procfile in the
current working directory and fail with:

    ERROR: open Procfile: no such file or directory
"""
import docker

docker_client = docker.from_env()


def test_starts_with_overridden_workdir(docker_compose):
    container = docker_client.containers.get("nginx-proxy")
    assert container.status == "running"
    assert b"open Procfile: no such file or directory" not in container.logs()
