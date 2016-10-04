# kartograafr
ArcGIS/Canvas data bridge

## Name
Questions are often asked about the name of this application.  **kartograafr** (*never capitalized*) is loosely based on the Dutch word "cartograaf", which means "cartographer" in English.  Some artistic license was taken to make the name more unique.  Since kartograafr is written in Python, a language created by a Dutch application developer (Guido van Rossum), it's only fitting.

## Purpose
The kartograafr application...

* searches for Canvas courses and their assignments which are associated with a specific Canvas outcome object,
* creates or updates ArcGIS groups that contain the users of the Canvas courses it found,
* reads part of its configuration from a page in a specific Canvas course used only for this purpose, 
* can be easily updated by changing its configuration course page in Canvas,
* allows support staff to update its configuration without requiring sysadmin access
 
 
## Setup and Installation

0. In Canvas:
    0. Make note of the Canvas API base URL
    0. Make note of the Canvas account ID number being used for the following items
    0. Prepare an API access token
    0. Create an ArcGIS outcome and note its ID number
    0. Create a kartograafr configuration course and note its ID number
        0. Create a page named `course-ids`
        0. Add to the page the URLs of courses to be processed (they will appear as links on the page)
        0. Give support staff the permissions necessary to update that page
0. In ArcGIS:
    0. Make note of the organization name being used (e.g., `devumich` or `umich`)
    0. Create a user with permission to create and modify user groups, make note of the username and password
0. Install from GitHub (https://github.com/tl-its-umich-edu/kartograafr) into `/usr/local/apps/kartograafr` on server
0. Update `/usr/local/apps/kartograafr/config.py` as necessary
    0. Add configuration values from Canvas
        0. API base URL and token
        0. Account ID number
        0. ArcGIS outcome ID number
        0. kartograafr configuration course ID number
        0. kartograafr configuration course page name (i.e., `course-ids`)
        0. *Optional*: Add a set of course IDs to process.  This is used as a backup if the configuration course page is misformatted or corrupted.  It may also be used *in place of* the configuration course and page.
    0. Add configuration values from ArcGIS
        0. Organization name
        0. Username and password
    0. Review email and logging settings and update them        
0. Set up the cron jobs
    0. Copy `rootdir_etc_cron.d/kartograafr` from the installation directory to `/etc/cron.d/kartograafr`
    0. Edit `/etc/cron.d/kartograafr` to use the desired schedule and correct sysadmin email address for errors

