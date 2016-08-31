from os import linesep

import arcrest
from arcresthelper import securityhandlerhelper

import config as umichConfig

# config = {
#     'username': '',
#     'password': '',
#     'security_type': 'Portal',  # Default: "Portal". "Required option" by bug in some ArcREST versions.
# }

config = umichConfig.ArcGIS.SECURITYINFO

token = securityhandlerhelper.securityhandlerhelper(config)  # why does this print "'http'"!?
admin = arcrest.manageorg.Administration(securityHandler=token.securityhandler)
content = admin.content
userInfo = content.users.user()
print(linesep.join(map(str, userInfo.folders)))
