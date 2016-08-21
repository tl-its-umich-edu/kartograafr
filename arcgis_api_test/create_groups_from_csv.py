"""
   This sample shows how to create groups from a
   csv files, sample csv and icon provided in the
   create_groups_support_material.zip

"""
import csv
import os
import json

from arcresthelper import orgtools


def trace():
    """
        trace finds the line, the filename
        and error message and returns it
        to the user
    """
    import traceback, inspect, sys
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    filename = inspect.getfile(inspect.currentframe())
    # script name + line number
    line = tbinfo.split(", ")[1]
    # Get Python syntax error
    #
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror


if __name__ == "__main__":
    securityinfo = {
        'security_type': 'Portal',  # LDAP, NTLM, OAuth, Portal, PKI,
        'username': '',
        'password': '',
        'org_url': "http://www.arcgis.com",
        'proxy_url': None,
        'proxy_port': None,
        'referer_url': None,
        'token_url': None,
        'certificatefile': None,
        'keyfile': None,
        'client_id': None,
        'secret_id': None,
    }
    csvgroups = r'groups.csv'
    pathtoicons = r""

    try:
        orgt = orgtools.orgtools(securityinfo=securityinfo)

        if orgt.valid == False:
            print orgt.message
        else:
            print 'opening file...'
            if os.path.isfile(csvgroups):
                with open(csvgroups, 'rb') as csvfile:

                    for row in csv.DictReader(csvfile, dialect='excel'):
                        print row
                        print json.dumps(row, indent=2, sort_keys=True)
                        if ('thumbnail' in row) and (os.path.isfile(os.path.join(pathtoicons, row['thumbnail']))):
                            thumbnail = os.path.join(pathtoicons, row['thumbnail'])
                            if not os.path.isabs(thumbnail):
                                sciptPath = os.getcwd()
                                thumbnail = os.path.join(sciptPath, thumbnail)

                            result = orgt.createGroup(
                                title=row['title'], description=row['description'],
                                tags=row['tags'],
                                snippet=row['snippet'], phone=row['phone'], access=row['access'],
                                sortField=row['sortField'], sortOrder=row['sortOrder'],
                                isViewOnly=row['isViewOnly'],
                                isInvitationOnly=row['isInvitationOnly'], thumbnail=thumbnail)

                        else:
                            result = orgt.createGroup(
                                title=row['title'], description=row['description'],
                                tags=row['tags'],
                                snippet=row['snippet'], phone=row['phone'], access=row['access'],
                                sortField=row['sortField'], sortOrder=row['sortOrder'],
                                isViewOnly=row['isViewOnly'],
                                isInvitationOnly=row['isInvitationOnly'])

                        if result is None:
                            pass
                        else:
                            print "Group created: " + result.title
    except:
        line, filename, synerror = trace()
        print "error on line: %s" % line
        print "error in file name: %s" % filename
        print "with error message: %s" % synerror
