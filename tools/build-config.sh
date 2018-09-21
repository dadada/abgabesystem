#!/bin/sh

cat > python-gitlab.cfg <<EOF
[global]
default = default
ssl_verify = true

[default]
url = $(echo ${CI_PROJECT_URL} | cut -d '/' -f -3)
api_version = 4
private_token = ${PRIVATE_API_TOKEN}
EOF
