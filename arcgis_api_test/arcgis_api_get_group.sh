#!/bin/sh --

if [ $# -lt 1 ]; then
  echo "Usage: $0 token" > /dev/stderr
  exit 1
fi

token="$1"

#
# Original query saved from Google Chrome
#

#curl 'https://www.arcgis.com/sharing/rest/community/groups?num=20&start=0&sortField=modified&sortOrder=desc&q=agolcanvas&f=json&token=' \
#-H 'Pragma: no-cache' \
#-H 'Origin: https://developers.arcgis.com' \
#-H 'Accept-Encoding: gzip, deflate, sdch, br' \
#-H 'Accept-Language: en-US,en;q=0.8' \
#-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36' \
#-H 'Content-Type: application/x-www-form-urlencoded' \
#-H 'Accept: */*' \
#-H 'Cache-Control: no-cache' \
#-H 'Referer: https://developers.arcgis.com/javascript/3/samples/portal_getgroupamd/' \
#-H 'Connection: keep-alive' \
#--compressed

#
# Shortened query
#

curl 'https://www.arcgis.com/sharing/rest/community/groups?num=20&start=0&sortField=modified&sortOrder=desc&q=agolcanvas&f=json&token='$token \
--compressed
