#!/bin/bash

# Remove "bats-*" containers
function teardown {
	docker rm -f $(docker ps -aq -f name=bats-*)
}

teardown
