.SILENT :
.PHONY : test test2

update-dependencies:
	docker pull jwilder/docker-gen:0.7.3
	docker pull nginx:1.11.9
	docker pull nginx:1.11.9-alpine
	docker pull python:3
	docker pull rancher/socat-docker:latest
	docker pull appropriate/curl:latest
	docker pull docker:1.10

test-debian:
	docker build -t jwilder/nginx-proxy:bats .
	bats test

test-alpine:
	docker build -f Dockerfile.alpine -t jwilder/nginx-proxy:bats .
	bats test

test: test-debian test-alpine

test2-debian:
	$(MAKE) -C test2 test-debian

test2-alpine:
	$(MAKE) -C test2 test-alpine
