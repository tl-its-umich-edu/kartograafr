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

----------------

## Running as a service

### For Administrators: Setup and Installation
##### Docker instance configuration

The kartograafr service runs in a Docker container.  Configuring
the container requires setting values in three files: **config.py**
and **secrets.py** and kartograafr cron tab file **kartograafr**.

The **config.py** file  contains environment values for the Canvas and
ArcGIS and mail server connections and log file names.  It also contains information on
where to get assignment information within the Canvas instance.
This file contains dummy values for api tokens, account names and passwords.
These values are overridden in the **secrets.py** file.

Since different configurations are required for development and
production there are multiple copies of the config.py and crontab file
in source control under instance appropriate names.  The Docker
container uses an initialization script that will install the
appropriate files for the container.  See below.



##### Initial Canvas configuration

1. In Canvas:
    1. Make note of the Canvas API base URL
    1. Make note of the Canvas account ID number being used for the following items
    1. Prepare an API access token
    1. Create an outcome for ArcGIS and note its ID number
    1. Create a kartograafr configuration course and note its ID number
        1. Create a page named `course-ids`
        1. Add to the page the URLs of courses to be processed (they will appear as links on the page)
        1. Give support staff the permissions necessary to update that
        page (add them with the "Teacher" role)

##### Initial ArcGIS configuration
1. In ArcGIS:
    1. Make note of the organization name being used (e.g., `devumich` or `umich`)
    1. Create a user with permission to create and modify user groups,
    make note of the username and password

##### Python configuration
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



### For Instructors
#### Designate Course and Assignments To Be Synchronized

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

----------------

## Development

### Python Environment / ArcGIS / Anaconda

The newest release of the ArcGIS Python API is only distributed via
the Anaconda environment manager.  For local development you'll need
to install Anaconda (see https://www.anaconda.com/download) and use it to create a virtual environment in Python 3.
```
conda create --name py35 python=3.5
source activate py35
```

Once Anaconda is installed and Python 3 virtual environment is created
and activated
install the ArcGIS api by running  
```
conda install -c esri arcgis
```
Also install any required packages by running:
```
pip install -r requirements.text
```

Note that this python environment must be used in testing or running kartograafr.

### Testing Locally

To run the kartograafr scan of ArcGIS a single time from the local machine (not Docker) and check the python installation, use:
```
USE_CONDA_ENV=py35 ./startup.sh
```

Some local files must be available for local testing. The exact
locations of the files is specified by your local configuration.  **The
log configuration in config.py must point to existing directories.** This may require creating the /var/log/kartograafr directory and setting permissions to be universally writeable.
The **secrets.py** file must be available from a directory that has
been added to the PYTHONPATH.

#### Local mail server

When testing locally you can setup a mock email server for
testing. Typically a Python installation provides a debugging smtpd
that can be started with the command:

```
python -m smtpd -n -c DebuggingServer localhost:1025
```

#### Starting kartograafr

A *startup.sh* script is now provided to invoke kartagraafr.  This
script can be run from the OSX command line or in a Docker container.
It automatically accounts for the environmental differences.  A
startup script is exceedingly helpful for running the program under
cron in Docker.  It's also very convenient in making it possible to
run kartograafr from the command line during development without
requiring running Docker.  One very important function of the startup
script is to make the *secrets* directory with the secure connection
information available to the application.  See the script for more
details.

kartograafr can also be run directly under Eclipse. The Eclipse
project will need to be setup to use the appropriate Ananconda virtual
environment.  It's likely to work with other IDEs but YMMV.


### Docker

#### Running kartograafr in  Docker locally

The *runDocker.sh* script will configure and build a local Docker
container for kartograafr and will setup a Docker environment that
allows running that container on OSX. This script  is not needed when running
on OpenShift since that provides a rich environment of services.
A Dockerfile is provided for local development. It assumes that the
code has been checked out already.  

To run on a local Docker environment, use
```
./runDocker.sh
```
This will display status information during setup, as well as the current crontab file to give information on scheduled runs. This can be used to determine when the next kartograafr scan should run. If errors are encountered when it runs or during the setup steps that are related to directory structure or file permissions on the Docker container, open another terminal window, navigate to the kartograafr folder, and use
```./dol bash``` to open bash in the Docker container. (The **dol** script contains shortcuts to run a number of commands on the local Docker container, when only a single container is running.)

#### Docker Considerations: Volatile Storage

Using Docker for the run time environment has some design implications, discussed below.

The running instance may be restarted at any time because of
maintenance or an administrative need to move a running instance to
different physical server. In addition if the application uses scaling to provide
capacity then additional copies of the instance may be started and removed
without warning.  This means that the instance should not rely on
storing critical information in memory. A running instance should not assume that it
is the only instance using data unless that restriction is part of the
run time configuration.

The file system in the instance is volatile.  The application can read
and write to the local file system but a restart will make those
changes vanish.  Docker *can* easily be configured to map external
persistant disk to internal file system directories but that must be
configured explicitly when invoking Docker.

### OpenShift

Applications that run under Docker are usually easy to run on
OpenShift.  There will be configuration changes.  OpenShift
configuration is beyond the scope of this readme.  The *runDocker.sh*
script is a model for what OpenShift needs to be configured to supply.

------

###  Secure Information

Any secure or authentication information needs to be
kept out of source control and be strictly separated from normal
properties.  That information is expected to be found in the
*secrets.py* module which will be available in a separate secrets directory.
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
