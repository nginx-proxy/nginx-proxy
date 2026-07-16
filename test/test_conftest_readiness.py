from types import SimpleNamespace

import pytest

import conftest


class FakeContainer:
    def __init__(
            self,
            name,
            image,
            *,
            environment=None,
            labels=None,
            logs=b"Watching docker events",
            worker_generations=None,
            reload_exit_code=0,
            running=True,
            web_probe_failures=0,
    ):
        self.name = name
        self.id = name
        self.attrs = {
            "Config": {
                "Image": image,
                "Env": environment or [],
                "Labels": labels or {},
            },
            "State": {"Running": running},
        }
        self._logs = logs
        self._worker_generations = worker_generations or [{"10"}, {"20"}]
        self._top_calls = 0
        self._reload_exit_code = reload_exit_code
        self._web_probe_failures = web_probe_failures
        self.exec_calls = []

    def logs(self, **kwargs):
        return self._logs

    def exec_run(self, command):
        self.exec_calls.append(command)
        if command == ["nginx", "-t"]:
            return SimpleNamespace(exit_code=0, output=b"configuration is valid")
        if command[0:2] == ["python3", "-c"]:
            if self._web_probe_failures:
                self._web_probe_failures -= 1
                return SimpleNamespace(exit_code=1, output=b"connection refused")
            return SimpleNamespace(exit_code=0, output=b"")
        return SimpleNamespace(exit_code=self._reload_exit_code, output=b"reload output")

    def reload(self):
        pass

    def top(self, **kwargs):
        index = min(self._top_calls, len(self._worker_generations) - 1)
        self._top_calls += 1
        processes = [
            [pid, "nginx: worker process"]
            for pid in sorted(self._worker_generations[index])
        ]
        return {"Titles": ["PID", "COMMAND"], "Processes": processes}


class FakeContainers:
    def __init__(self, containers):
        self._containers = containers
        self.filters = None

    def list(self, filters):
        self.filters = filters
        return self._containers


def test_wait_for_combined_proxy_reloads_and_waits_for_new_worker(monkeypatch):
    proxy = FakeContainer("proxy", "nginxproxy/nginx-proxy:test")
    containers = FakeContainers([proxy])
    monkeypatch.setattr(
        conftest, "docker_client", SimpleNamespace(containers=containers)
    )

    conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)

    assert containers.filters == {
        "status": "running",
        "label": "com.docker.compose.project=example",
    }
    assert proxy.exec_calls == [["nginx", "-t"], ["nginx", "-s", "reload"]]


def test_wait_for_separate_containers_honors_custom_nginx_label(monkeypatch):
    dockergen = FakeContainer(
        "dockergen",
        "nginxproxy/nginx-proxy:test-dockergen",
        environment=["NGINX_CONTAINER_LABEL=example.proxy"],
    )
    nginx = FakeContainer("nginx", "nginx:latest", labels={"example.proxy": ""})
    unrelated = FakeContainer("backend", "nginx:alpine")
    monkeypatch.setattr(
        conftest,
        "docker_client",
        SimpleNamespace(
            containers=FakeContainers([dockergen, nginx, unrelated])
        ),
    )

    conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)

    assert nginx.exec_calls == [["nginx", "-t"], ["nginx", "-s", "reload"]]
    assert dockergen.exec_calls == []
    assert unrelated.exec_calls == []


def test_wait_for_multiple_combined_proxies(monkeypatch):
    first = FakeContainer("first", "nginxproxy/nginx-proxy:test")
    second = FakeContainer("second", "nginxproxy/nginx-proxy:test")
    monkeypatch.setattr(
        conftest,
        "docker_client",
        SimpleNamespace(containers=FakeContainers([first, second])),
    )

    conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)

    expected_calls = [["nginx", "-t"], ["nginx", "-s", "reload"]]
    assert first.exec_calls == expected_calls
    assert second.exec_calls == expected_calls


def test_waits_for_web_ports_without_requesting_through_nginx(monkeypatch):
    proxy = FakeContainer("proxy", "nginxproxy/nginx-proxy:test")
    backend = FakeContainer(
        "backend",
        "web",
        environment=["WEB_PORTS=81 82"],
        web_probe_failures=1,
    )
    monkeypatch.setattr(
        conftest,
        "docker_client",
        SimpleNamespace(containers=FakeContainers([proxy, backend])),
    )

    conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)

    probe_calls = [call for call in backend.exec_calls if call[0:2] == ["python3", "-c"]]
    assert len(probe_calls) == 2
    assert probe_calls[-1][-2:] == ["81", "82"]


def test_ignores_proxy_that_exits_before_docker_gen_is_ready(monkeypatch):
    healthy = FakeContainer("healthy", "nginxproxy/nginx-proxy:test")
    invalid = FakeContainer(
        "invalid",
        "nginxproxy/nginx-proxy:test",
        logs=b"invalid configuration",
        running=False,
    )
    monkeypatch.setattr(
        conftest,
        "docker_client",
        SimpleNamespace(containers=FakeContainers([healthy, invalid])),
    )

    conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)

    assert healthy.exec_calls == [["nginx", "-t"], ["nginx", "-s", "reload"]]
    assert invalid.exec_calls == []


def test_reload_failure_is_not_silently_ignored():
    nginx = FakeContainer(
        "nginx", "nginxproxy/nginx-proxy:test", reload_exit_code=1
    )

    with pytest.raises(RuntimeError, match="Failed to reload nginx in nginx"):
        conftest._reload_nginx_and_wait(
            nginx, conftest.time.monotonic() + 1, 0
        )


def test_worker_replacement_timeout_is_not_silently_ignored():
    nginx = FakeContainer(
        "nginx",
        "nginxproxy/nginx-proxy:test",
        worker_generations=[{"10"}],
    )

    with pytest.raises(RuntimeError, match="Timed out waiting for new nginx workers"):
        conftest._reload_nginx_and_wait(
            nginx, conftest.time.monotonic() + 0.01, 0
        )


def test_missing_proxy_role_is_an_error(monkeypatch):
    backend = FakeContainer("backend", "nginx:alpine")
    monkeypatch.setattr(
        conftest,
        "docker_client",
        SimpleNamespace(containers=FakeContainers([backend])),
    )

    with pytest.raises(RuntimeError, match="Could not find both docker-gen and nginx"):
        conftest.wait_for_nginxproxy_to_be_ready("example", timeout=1, interval=0)
