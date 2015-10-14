.SILENT :
.PHONY : test

test:
	docker build -t jwilder/nginx-proxy:bats .
	bats test
