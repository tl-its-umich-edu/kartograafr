# kartograafr
ArcGIS/Canvas data bridge

# NOTES:
Probably need to install Anaconda as separate environment to run
native on OSX and to run inside eclipse.  See https://docs.anaconda.com/anaconda/user-guide/tasks/integration/eclipse-pydev

anaconda comes with pip and can create virtual environments

activate anaconda environment with something like:
*${BASE_ANACONDA}/bin/activate <env name>*

Where BASE_ANACONDA is a base anaconda install
like:. ~/dev/ANACONDA/anaconda3

Get  a list of all the anaconda environments with: *conda info --envs*
You will need to setup some anaconda environment to use conda.
You can use *...../activate* without specifying an environment to use
the "root" environment.


Where BASE_ANACONDA is a base installation env like:  . ~/dev/ANACONDA/anaconda3/bin/activate conda-python-3

need install the arcgis api: **conda install -c esri arcgis**

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


## Running in Docker and on Command line

Two new scripts have been provided to make running kartograafr smoother.

As of 11/2017 kartograafr is able to run in a Docker container.  The
*runDocker.sh* script will configure and build a Docker container for
kartograafr and will setup a Docker environment that allows running that
container on OSX. When running on OpenShift that enviroment provides
the build, deployment, and environmental services the application
requires.

A *startup.sh* script is now provided to invoke kartagraafr.  This
script can be run from the OSX command line or in a Docker container.
It automatically accounts for the environmental differences.  A
startup script is exceedingly helpful for running the program under
cron in Docker.  It's also very convenient in making it possible to
run kartograafr from the command line during development without
requiring running Docker.  One very important function of the startup
script is to make the *secrets* directory with the secure connection
information available to the application.

## Secrets

For OpenShift any secure or authentication information needs to be
kept out of source control and be strictly separated from normal
properties.  That information is now expected to be found in the
*secrets.py* module which will be available in a seperate directory.
A template for a secrets file is in the the configuration directory.
That template shouldn't be modified but should be copied and that copy
should be read from the separate secure directory.

When running locally the *startup.sh* script assumes that the
secrets.py file is available in the subdirectory *./OPT/SECRETS*.
That reference can be a symbolic link to the actual location.  On
OpenShift the location will be set in the deployment
configuration. See the OpenShift kartograafr dev project to see how it
is configured.

The template file illustrates how to easily implement an environmental variable
override of the property value.  The code given is very likely not the
best way to do this and is likely to be improved soon.

Rather than creating / modifying OpenShift secrets by hand the script
*os-updateSecret.sh* can be used to update or create a secret.  It
will upload the contents of a directory to a special volume available
to the application in OpenShift. Note that the application will need
to be redeployed to pick up any changes in the values of the secrets.

## For Administrators: Setup and Installation

1. In Canvas:
    1. Make note of the Canvas API base URL
    1. Make note of the Canvas account ID number being used for the following items
    1. Prepare an API access token
    1. Create an outcome for ArcGIS and note its ID number
    1. Create a kartograafr configuration course and note its ID number
        1. Create a page named `course-ids`
        1. Add to the page the URLs of courses to be processed (they will appear as links on the page)
        1. Give support staff the permissions necessary to update that page (add them with the "Teacher" role)
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
    
    
## Development and Debugging
  To handle email you can use the debugging smtpd provided with python via the command:
  
<code>
    python -m smtpd -n -c DebuggingServer localhost:1025
</code>

## Docker
A Dockerfile is provided for local development. It assumes that the
code has been checked out already.  The log goes to a
disk file instead of stdout.

## For Instructors: Designate Course and Assignments To Be Synchronized

1. Email `4-HELP@umich.edu` to request that your course be added to the list of courses on the "kartograafr: Canvas/ArcGIS Integration" configuration page.  This will only need to be requested once for each of your courses.  You may proceed to the next step while you wait for this request to be fulfilled.
1. Add the "ArcGIS Group" outcome to your course.  This will only need to be done once for each of your courses.
    1. On your course's home page, click the "Outcomes" navigation item.
    1. On your course's Outcome page, click the "🔍 Find" button.  (Note: **_DO NOT_** click the "+ Outcome" button.)
    1. In the dialog box that appears, select the following list items, in order:
        1. "Account Standards"
        1. "University of Michigan - Ann Arbor"
        1. "ArcGIS"
        1. "ArcGIS Group".  (Note: Only click the "ArcGIS Group" item in the list immediately to the right of the "ArcGIS" item.  **_DO NOT_** click on the larger "ArcGIS Group" link that appears in the wider space in the rightmost part of the dialog box.)
    1. At the bottom right corner of the dialog box, click the "Import" button.
    1. In the alert box with the message "Import outcome 'ArcGIS Group' to group '_your course name here_'?", click the "OK" button.
    1. After the import is complete, you will see "ArcGIS Group" in your course's list of outcomes.
1. Each of your course's assignments which are to be synchronized with ArcGIS Online needs to include the "ArcGIS Group" outcome in their rubrics.  **_You will need to do this for each new assignment you add to the course._**  
    
    This can be simplified somewhat by adding the "ArcGIS Group" outcome to a single rubric that will be used by multiple assignments.  Each assignment that uses that rubric will automatically include the "ArcGIS Group" outcome.  It's recommended that rubrics should be given meaningful names.  For example, a good name could be "_your course name here_ Rubric (with ArcGIS sync)".
    1. Click on the name of an assignment in the list of your course's assignments.
    1. Edit the assignment's rubric (or add a new rubric if one doesn't already exist).
    1. Click on "🔍 Find Outcome".
    1. In the dialog box of your course's outcomes that appears, click "ArcGIS Group" in the list on the left side of the box.  (Note: **_DO NOT_** click on the larger "ArcGIS Group" link that appears in the wider space to the right of the list.)
    1. At the bottom right corner of the dialog box, click the "Import" button.
    1. In the alert box with the message "Import outcome 'ArcGIS Group' to group '_your course name here_'?", click the "OK" button.
    1. After the import is complete, you will see "ArcGIS Group" as part of the assignment's rubric.
    1. Finally, click the "Update Rubric" button (or the "Create Rubric" button if you were adding a new rubric).
1. Control the synchronization of your assignment with ArcGIS online by setting the "Available From", "Until", and "Due Date" times.
1. Once all of the above requirements are satisfied, kartograafr will synchronize your course's assignments with ArcGIS Online.  It will happen automatically, several times each day.  You will receive email a few times each day showing the results of the synchronizations.

# Python 2 to Python 3 (in process) 
1. update may include/require unicode changes since P3 does unicode by default. (under consideration)
1. run 2to3 script
1. change print statements to function calls.
1. For RequestPlus copy urlnorm.py from standard-packages and make some p3 updates. It is not a module and isn't P3 compatible.  Not yet clear if it works cleanly
1. requirements.txt take out requirement for python >= 2.7.5
1. util.py - change methodName args (drop depth), change name of "object" as parameter name.
