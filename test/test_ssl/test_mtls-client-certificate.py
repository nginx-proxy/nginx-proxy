import pathlib

import pytest
from requests.exceptions import SSLError


@pytest.fixture(scope="session")
def clientcerts():
    """
    Pytest fixture to provide paths to client certificates and keys.
    """
    current_file_path = pathlib.Path(__file__)
    clientcerts_path = current_file_path.parent.joinpath("clientcerts")
    
    return {
        "valid_client_cert": clientcerts_path.joinpath("Valid.crt"),
        "valid_client_key": clientcerts_path.joinpath("Valid.key"),
        "revoked_client_cert": clientcerts_path.joinpath("Revoked.crt"),
        "revoked_client_key": clientcerts_path.joinpath("Revoked.key"),
    }

@pytest.mark.parametrize("description, url, cert, expected_code, expected_text", [
    #Enforced: Test connection to a website with mTLS enabled without providing a client certificate.
    ("Enforced: No client certificate, virtual_host", "https://mtls-enabled.nginx-proxy.tld/port", None, 400, "400 No required SSL certificate was sent"),
    ("Enforced: No client certificate, virtual_path", "https://mtls-enabled.nginx-proxy.tld/bar/port", None, 400, "400 No required SSL certificate was sent"),
    ("Enforced: No client certificate, regex", "https://regex.nginx-proxy.tld/port", None, 400, "400 No required SSL certificate was sent"),
    ("Enforced: No client certificate, global CA", "https://global-mtls-enabled.nginx-proxy.tld/port", None, 400, "400 No required SSL certificate was sent"),
    #Authenticated: Test connection to a website with mTLS enabled providing a valid client certificate.
    ("Authenticated: Valid client certificate, virtual_host", "https://mtls-enabled.nginx-proxy.tld/port", "valid", 200, "answer from port 81\n"),
    ("Authenticated: Valid client certificate, virtual_path", "https://mtls-enabled.nginx-proxy.tld/bar/port", "valid", 200, "answer from port 83\n"),
    ("Authenticated: Valid client certificate, regex", "https://regex.nginx-proxy.tld/port", "valid", 200, "answer from port 85\n"),
    ("Authenticated: Valid client certificate, global CA", "https://global-mtls-enabled.nginx-proxy.tld/port", "valid", 200, "answer from port 81\n"),
    #Revoked: Test connection to a website with mTLS enabled providing a revoked client certificate on the CRL.
    ("Revoked: Invalid client certificate, virtual_host", "https://mtls-enabled.nginx-proxy.tld/port", "revoked", 400, "400 The SSL certificate error"),
    ("Revoked: Invalid client certificate, virtual_path", "https://mtls-enabled.nginx-proxy.tld/bar/port", "revoked", 400, "400 The SSL certificate error"),
    ("Revoked: Invalid client certificate, regex", "https://regex.nginx-proxy.tld/port", "revoked", 400, "400 The SSL certificate error"),
    ("Revoked: Invalid client certificate, global CA", "https://global-mtls-enabled.nginx-proxy.tld/port", "revoked", 400, "400 The SSL certificate error"),
    #Optional: Test connection to a website with optional mTLS. Access is not blocked but can be controlled with "$ssl_client_verify" directive. We assert on /foo if $ssl_client_verify = SUCCESS response with status code 418.
    ("Optional, Not enforced: No client certificate", "https://mtls-optional.nginx-proxy.tld/port", None, 200, "answer from port 82\n"),
    ("Optional: Enforced, Valid client certificate", "https://mtls-optional.nginx-proxy.tld/foo/port", "valid", 418, "ssl_client_verify is SUCCESS"),
    ("Optional, Not enforced: No client certificate", "https://mtls-optional.nginx-proxy.tld/bar/port", None, 200, "answer from port 84\n"),
    ("Optional: Enforced, Valid client certificate", "https://mtls-optional.nginx-proxy.tld/foo/bar/port", "valid", 418, "ssl_client_verify is SUCCESS"),
    ("Optional, Not enforced: No client certificate, global CA", "https://global-mtls-optional.nginx-proxy.tld/port", None, 200, "answer from port 82\n"),
    ("Optional: Enforced, Valid client certificate, global CA", "https://global-mtls-optional.nginx-proxy.tld/foo/port", "valid", 418, "ssl_client_verify is SUCCESS"),
])
def test_mtls_client_certificates(docker_compose, nginxproxy, clientcerts, description, url, cert, expected_code, expected_text):
    """
    Parameterized test for mTLS client certificate scenarios.
    """
    if cert == "valid":
        client_cert = (clientcerts["valid_client_cert"], clientcerts["valid_client_key"])
    elif cert == "revoked":
        client_cert = (clientcerts["revoked_client_cert"], clientcerts["revoked_client_key"])
    else:
        client_cert = None

    r = nginxproxy.get(url, cert=client_cert if client_cert else None)
    assert r.status_code == expected_code
    assert expected_text in r.text
