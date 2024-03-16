import pytest
import logging
import time

def test_forwards_to_web1(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web1.nginx-proxy.example/port")
    assert r.status_code == 200
    assert r.text == "answer from port 81\n"

def test_nginx_config_remains_the_same_after_restart(docker_compose, nginxproxy):
    """
    Restarts the Web container and returns nginx-proxy config after restart
    """
    def get_conf_after_web_container_restart():
        web_containers = docker_compose.containers.list(filters={"ancestor": "web:latest"})
        assert len(web_containers) == 1
        web_containers[0].restart()
        time.sleep(3)

        return nginxproxy.get_conf()

    config_before_restart = nginxproxy.get_conf()

    for i in range(1, 8):
        logging.info(f"Checking for the {i}-st time that config is the same")
        config_after_restart = get_conf_after_web_container_restart()
        if config_before_restart != config_after_restart:
            logging.debug(f"{config_before_restart!r} \n\n {config_after_restart!r}")
            pytest.fail("nginx-proxy config before and after restart of a web container does not match", pytrace=False)
