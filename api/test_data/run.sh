#!/bin/sh
set -ex

mkdir -p /tmp/hca
mongod --verbose --config ./mongodb.conf
