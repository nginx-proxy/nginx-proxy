.SILENT :
.PHONY : test-debian test-alpine test


build-webserver:
	docker build --pull -t web test/requirements/web

build-nginx-proxy-test-debian:
	docker build --pull --build-arg NGINX_PROXY_VERSION="test" -f Dockerfile.debian -t nginxproxy/nginx-proxy:test .

build-nginx-proxy-test-alpine:
	docker build --pull --build-arg NGINX_PROXY_VERSION="test" -f Dockerfile.alpine -t nginxproxy/nginx-proxy:test .

build-nginx-proxy-test-dockergen:
	docker build --pull --build-arg NGINX_PROXY_VERSION="test" -f Dockerfile.dockergen -t nginxproxy/nginx-proxy:test-dockergen .

test-debian: export COMPOSE_PROFILES = singleContainer
test-debian: build-webserver build-nginx-proxy-test-debian
	test/pytest.sh

test-alpine: export COMPOSE_PROFILES = singleContainer
test-alpine: build-webserver build-nginx-proxy-test-alpine
	test/pytest.sh

test-dockergen: export COMPOSE_PROFILES = separateContainers
test-dockergen: build-webserver build-nginx-proxy-test-docker-gen
	test/pytest.sh

test: test-debian test-alpine test-dockergen
