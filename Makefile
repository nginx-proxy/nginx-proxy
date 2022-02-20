.SILENT :
.PHONY : test-debian test-alpine test


build-webserver:
	docker build -t web test/requirements/web

build-nginx-proxy-test-debian:
	docker build --build-arg NGINX_PROXY_VERSION="test" -t nginxproxy/nginx-proxy:test .

build-nginx-proxy-test-alpine:
	docker build --build-arg NGINX_PROXY_VERSION="test" -f Dockerfile.alpine -t nginxproxy/nginx-proxy:test .

test-debian: build-webserver build-nginx-proxy-test-debian
	test/pytest.sh

test-alpine: build-webserver build-nginx-proxy-test-alpine
	test/pytest.sh

test: test-debian test-alpine
