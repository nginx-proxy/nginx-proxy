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

test-debian: build-webserver build-nginx-proxy-test-debian build-nginx-proxy-test-dockergen
	test/pytest.sh

test-alpine: build-webserver build-nginx-proxy-test-alpine build-nginx-proxy-test-dockergen
	test/pytest.sh

test: test-debian test-alpine
