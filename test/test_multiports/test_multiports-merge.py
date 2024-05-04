import backoff
import pytest


def test_multiports_and_legacy_configs_should_be_merged(docker_compose, nginxproxy):
    @backoff.on_predicate(backoff.constant, lambda r: r == False, interval=.5, max_tries=20, jitter=None)
    def answer_contains(answer, url):
        return answer in nginxproxy.get(url).text

    assert answer_contains("80", "http://merged.nginx-proxy.tld/port")
    assert answer_contains("81", "http://merged.nginx-proxy.tld/port")

    assert answer_contains("9090", "http://merged.nginx-proxy.tld/foo/port")
    assert answer_contains("9191", "http://merged.nginx-proxy.tld/foo/port")
