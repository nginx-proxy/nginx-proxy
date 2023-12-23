import logging
import os
from os.path import join, isfile
from shutil import copy
from time import sleep

import pytest
from requests import ConnectionError

script_dir = os.path.dirname(__file__)

pytestmark = pytest.mark.xfail()  # TODO delete this marker once those issues are fixed

@pytest.fixture(scope="module", autouse=True)
def certs():
    """
    pytest fixture that provides cert and key files into the tmp_certs directory
    """
    file_names = ("web.nginx-proxy.crt", "web.nginx-proxy.key")
    logging.info("copying server cert and key files into tmp_certs")
    for f_name in file_names:
        copy(join(script_dir, "certs", f_name), join(script_dir, "tmp_certs"))
    yield
    logging.info("cleaning up the tmp_cert directory")
    for f_name in file_names:
        if isfile(join(script_dir, "tmp_certs", f_name)):
            os.remove(join(script_dir, "tmp_certs", f_name))

###############################################################################


def test_unknown_virtual_host_is_503(docker_compose, nginxproxy):
    r = nginxproxy.get("http://foo.nginx-proxy/")
    assert r.status_code == 503


def test_http_web_is_301(docker_compose, nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy/port", allow_redirects=False)
    assert r.status_code == 301


def test_https_web_is_200(docker_compose, nginxproxy):
    r = nginxproxy.get("https://web.nginx-proxy/port")
    assert r.status_code == 200
    assert "answer from port 81\n" in r.text


@pytest.mark.incremental
def test_delete_cert_and_restart_reverseproxy(docker_compose):
    os.remove(join(script_dir, "tmp_certs", "web.nginx-proxy.crt"))
    docker_compose.containers.get("reverseproxy").restart()
    sleep(3)  # give time for the container to initialize
    assert "running" == docker_compose.containers.get("reverseproxy").status


@pytest.mark.incremental
def test_unknown_virtual_host_is_still_503(nginxproxy):
    r = nginxproxy.get("http://foo.nginx-proxy/")
    assert r.status_code == 503


@pytest.mark.incremental
def test_http_web_is_now_200(nginxproxy):
    r = nginxproxy.get("http://web.nginx-proxy/port", allow_redirects=False)
    assert r.status_code == 200
    assert "answer from port 81\n" == r.text


@pytest.mark.incremental
def test_https_web_is_now_broken_since_there_is_no_cert(nginxproxy):
    with pytest.raises(ConnectionError):
        nginxproxy.get("https://web.nginx-proxy/port")
