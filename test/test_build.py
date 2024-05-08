"""
Test that nginx-proxy-tester can build successfully
"""
import pytest
import docker
import re
import os

client = docker.from_env()

@pytest.fixture(scope = "session")
def docker_build(request):
    # Define Dockerfile path
    dockerfile_path = os.path.join(os.path.dirname(__file__), "requirements/")
    dockerfile_name = "Dockerfile-nginx-proxy-tester"

    # Build the Docker image
    image, logs = client.images.build(
        path = dockerfile_path,
        dockerfile = dockerfile_name,
        rm = True,  # Remove intermediate containers
        tag = "nginx-proxy-tester-ci",  # Tag for the built image
    )

    # Check for build success
    for log in logs:
        if "stream" in log:
            print(log["stream"].strip())
        if "error" in log:
            raise Exception(log["error"])

    def teardown():
        # Clean up after teardown
        client.images.remove(image.id, force=True)

    request.addfinalizer(teardown)

    # Return the image name
    return "nginx-proxy-tester-ci"

def test_build_nginx_proxy_tester(docker_build):
    assert docker_build == "nginx-proxy-tester-ci"

def test_run_nginx_proxy_tester(docker_build):
    # Run the container with 'pytest -v' command to output version info
    container = client.containers.run("nginx-proxy-tester-ci",
        command = "pytest -V",
        detach = True,
    )

    # Wait for the container to finish and get the exit code
    result = container.wait()
    exit_code = result.get("StatusCode", 1)  # Default to 1 (error) if not found

    # Get the output logs from the container
    output = container.logs().decode("utf-8").strip()

    # Clean up: Remove the container
    container.remove()

    # Assertions
    assert exit_code == 0, "Container exited with a non-zero exit code"
    assert re.search(r"pytest\s\d+\.\d+\.\d+", output)
