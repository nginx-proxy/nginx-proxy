dist: trusty
sudo: required

env:
  matrix:
  - TEST_TARGET: test-debian
  - TEST_TARGET: test-alpine

before_install:
  - sudo apt-get -y remove docker docker-engine docker-ce
  - sudo rm /etc/apt/sources.list.d/docker.list
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  - sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  - sudo apt-get update
  - sudo apt-get -y install docker-ce
  - docker version
  - docker info
  # prepare docker test requirements
  - make update-dependencies

script:
  - make $TEST_TARGET
