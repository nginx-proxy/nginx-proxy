.SILENT :
.PHONY : test-debian test-alpine test


update-dependencies:
	requirements/build.sh

test-debian: update-dependencies
	docker build -t jwilder/nginx-proxy:test ..
	./test.sh -v

test-alpine: update-dependencies
	docker build -f ../Dockerfile.alpine -t jwilder/nginx-proxy:test ..
	./test.sh -v

test: test-debian test-alpine
