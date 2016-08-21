import sys

# sys.path.append('/Users/lsloan/Projects/ArcGIS/sloanlance_ArcREST/src')

import arcrest
from arcresthelper import securityhandlerhelper

config = {
    'username': '',
    'password': '',
    # 'security_type': 'Portal', # due to bug, this default must be specified
}
token = securityhandlerhelper.securityhandlerhelper(config) # why does this print "'http'"!?
admin = arcrest.manageorg.Administration(securityHandler=token.securityhandler)
content = admin.content
userInfo = content.users.user()
userInfo.folders
