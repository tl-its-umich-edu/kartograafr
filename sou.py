from __future__ import print_function

from os import linesep

import requests
from bs4 import BeautifulSoup
from bs4.builder._htmlparser import HTMLParserTreeBuilder

import config

r = requests.get('https://umich.instructure.com:443/api/v1/courses/138596/pages/course-ids?'
                 'access_token=' + config.Canvas.API_AUTHZ_TOKEN)
soup = BeautifulSoup(r.json()['body'], builder=HTMLParserTreeBuilder())
print(linesep.join(a['href'] for a in soup.find_all('a')))
