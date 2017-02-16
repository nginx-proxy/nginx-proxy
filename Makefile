.SILENT :
.PHONY : test-debian test-alpine test


update-dependencies:
	test/requirements/build.sh

test-debian: update-dependencies
	docker build -t jwilder/nginx-proxy:test .
	test/pytest.sh

test-alpine: update-dependencies
	docker build -f Dockerfile.alpine -t jwilder/nginx-proxy:test .
	test/pytest.sh

test: test-debian test-alpine
