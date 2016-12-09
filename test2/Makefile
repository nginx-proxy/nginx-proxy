.SILENT :
.PHONY : test-debian test-alpine test


update-dependencies:
	requirements/build.sh
	pip install -U -r requirements.txt

test-debian: update-dependencies
	docker build -t jwilder/nginx-proxy:test ..
	pytest

test-alpine: update-dependencies
	docker build -f ../Dockerfile.alpine -t jwilder/nginx-proxy:test ..
	pytest

test: test-debian test-alpine
