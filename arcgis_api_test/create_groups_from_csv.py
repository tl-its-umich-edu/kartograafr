"""
   This sample shows how to create groups from a
   csv files, sample csv and icon provided in the
   create_groups_support_material.zip
"""
from __future__ import print_function

import csv
import json
import os

from arcresthelper import orgtools

import config
from util import CaptureStdoutLines

if __name__ == '__main__':
    # securityinfo = {
    #     'security_type': 'Portal',  # LDAP, NTLM, OAuth, Portal, PKI,
    #     'username': '',
    #     'password': '',
    #     'org_url': 'http://www.arcgis.com',
    #     'proxy_url': None,
    #     'proxy_port': None,
    #     'referer_url': None,
    #     'token_url': None,
    #     'certificatefile': None,
    #     'keyfile': None,
    #     'client_id': None,
    #     'secret_id': None,
    # }

    securityinfo = config.ArcGIS.SECURITYINFO

    csvgroups = r'groups.csv'
    pathToThumbnailFiles = r''

    orgt = orgtools.orgtools(securityinfo=securityinfo)

    if not orgt.valid:
        print(orgt.message)
    else:
        print('Opening file...')
        if os.path.isfile(csvgroups):
            with open(csvgroups, 'rb') as csvfile:

                for row in csv.DictReader(csvfile, dialect='excel'):
                    print(json.dumps(row, indent=2, sort_keys=True))
                    with CaptureStdoutLines() as output:
                        if 'thumbnail' in row:
                            thumbnail = os.path.join(pathToThumbnailFiles, row['thumbnail'])
                            if os.path.isfile(thumbnail):
                                if not os.path.isabs(thumbnail):
                                    thumbnail = os.path.join(os.getcwd(), thumbnail)
                                row['thumbnail'] = thumbnail

                        result = orgt.createGroup(**row)

                    if result is None:
                        print('Output:', os.linesep.join(output))
                    else:
                        print('Group created: "{}" (id: "{}")'.format(result.title, result.id))
