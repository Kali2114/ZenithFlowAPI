#!/bin/sh

set -e

envsub < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.com
nginx -git 'daemon off;'