#!/bin/sh --

curl 'https://www.arcgis.com/sharing/generateToken' \
-X POST \
-H 'Content-Type: application/x-www-form-urlencoded' \
--data 'request=getToken&username=&password=&expiration=60&referer=developers.arcgis.com&f=json'
