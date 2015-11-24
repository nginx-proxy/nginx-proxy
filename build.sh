#!/bin/bash

set -e

apt-get update

# Install python packages needed by simp_le
apt-get install -y -q --no-install-recommends python python-requests

# Install python packages needed to build  simp_le
apt-get install -y -q --no-install-recommends git gcc libssl-dev libffi-dev python-dev python-pip

# Get Let's Encrypt simp_le client source
git -C /opt clone https://github.com/kuba/simp_le.git

cd /opt/simp_le
# Upgrade setuptools
pip install -U setuptools
# Install simp_le in /usr/local/bin
python ./setup.py install

# Make house cleaning
rm -rf /opt/simp_le

apt-get autoremove -y git gcc libssl-dev libffi-dev python-dev python-pip

apt-get clean all
rm -r /var/lib/apt/lists/*
