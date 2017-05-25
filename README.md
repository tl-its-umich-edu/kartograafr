# kartograafr
ArcGIS/Canvas data bridge

## About
**_kartograafr_** — "kart-uh-GRAFF-fur", or in IPA: ['kɑr.toː.*ɣraːf.fər]

The name is based on the Dutch word for cartographer, "cartograaf", and was changed a little to make it unique.  It is never capitalized.  Since kartograafr is written in Python, a programming language created by a Dutch computer programmer (Guido van Rossum), a Dutch-based name is only fitting.

## Purpose
The kartograafr application...

* searches for Canvas courses and their assignments which are associated with a specific Canvas outcome object,
* creates or updates ArcGIS groups that contain the users of the Canvas course assignments it found,
* reads part of its configuration (course IDs to be checked) from a page in a specific Canvas course used only for this purpose, 
* can be easily updated by changing its configuration course page in Canvas,
* allows support staff to update its configuration via Canvas without requiring server sysadmin access
 
 
## Setup and Installation

1. In Canvas:
    1. Make note of the Canvas API base URL
    1. Make note of the Canvas account ID number being used for the following items
    1. Prepare an API access token
    1. Create an ArcGIS outcome and note its ID number
    1. Create a kartograafr configuration course and note its ID number
        1. Create a page named `course-ids`
        1. Add to the page the URLs of courses to be processed (they will appear as links on the page)
        1. Give support staff the permissions necessary to update that page
1. In ArcGIS:
    1. Make note of the organization name being used (e.g., `devumich` or `umich`)
    1. Create a user with permission to create and modify user groups, make note of the username and password
1. Install from GitHub (https://github.com/tl-its-umich-edu/kartograafr) into `/usr/local/apps/kartograafr` on server
1. Update `/usr/local/apps/kartograafr/config.py` as necessary
    1. Add configuration values from Canvas
        1. API base URL and token
        1. Account ID number
        1. ArcGIS outcome ID number
        1. kartograafr configuration course ID number
        1. kartograafr configuration course page name (i.e., `course-ids`)
        1. *Optional*: Add a set of course IDs to process.  This is used as a backup if the configuration course page is misformatted or corrupted.  It may also be used *in place of* the configuration course and page.
    1. Add configuration values from ArcGIS
        1. Organization name
        1. Username and password
    1. Review email and logging settings and update them        
1. Set up the cron jobs
    1. Copy `rootdir_etc_cron.d/kartograafr` from the installation directory to `/etc/cron.d/kartograafr`
    1. Edit `/etc/cron.d/kartograafr` to use the desired schedule and correct sysadmin email address for errors
