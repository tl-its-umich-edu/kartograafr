# kartograafr
ArcGIS/Canvas data bridge

## Table of Contents

1. [Overview](#overview)
    * About
    * Purpose
    * Use
1. [Configuration & Setup](#configurationAndSetup)
    * For Instructors
    * For Administrators & Developers
        * Canvas
        * ArcGIS
        * Application
1. [Installation & Development](#installationAndDevelopment)
    * Local Development
        * Sending Email
    * Docker
    * OpenShift

## <a name='overview'></a>Overview

### About
**_kartograafr_** — "kart-uh-GRAFF-fur", or in IPA: ['kɑr.toː.*ɣraːf.fər]

The name is based on the Dutch word for cartographer, "cartograaf", and was changed a little to make it unique. It is 
never capitalized. Since kartograafr is written in Python, a programming language created by a Dutch computer 
programmer (Guido van Rossum), a Dutch-based name is only fitting.

### Purpose
The kartograafr application ...

* searches for Canvas courses and their assignments that are associated with a specific Canvas outcome object
* creates and/or updates ArcGIS groups so that they contain the users of the Canvas course assignments found
* reads part of its configuration (course IDs to be checked) from a page in a specific Canvas course used only for this 
  purpose
* allows support staff to easily update via Canvas the courses to be synchronized with ArcGIS

### Use
kartograafr is maintained by ITS Teaching & Learning at the University of Michigan. The unit runs the service to 
support courses at the university that rely on ArcGIS for student assignments. Teaching & Learning currently runs the 
application as a scheduled job using [Docker](https://docs.docker.com/) containerization technology, the 
[OpenShift Container Platform](https://docs.openshift.com/), and an instance of the 
[Jenkins automation server](https://jenkins.io/doc/).

----------------

## <a name='configurationAndSetup'></a>Configuration & Setup

### For Instructors

The kartograafr service was designed so that it can be set up easily for a course by instructors and other support
staff. To designate a course and assignments in Canvas you would like synchronized with ArcGIS, do the following:

1. Email `4-HELP@umich.edu` to request that your course be added to the list of courses on the "kartograafr: 
   Canvas/ArcGIS Integration" configuration page. This will only need to be requested once for each of your courses. 
   You may proceed to the next step while you wait for this request to be fulfilled.
1. Add the "ArcGIS Group" outcome to your course. This will only need to be done once for each of your courses.
    1. On your course's home page, click the "Outcomes" navigation item.
    1. On your course's Outcome page, click the "🔍 Find" button. (Note: **_DO NOT_** click the "+ Outcome" button.)
    1. In the dialog box that appears, select the following list items, in order:
        1. "Account Standards"
        1. "University of Michigan - Ann Arbor"
        1. "ArcGIS"
        1. "ArcGIS Group". (Note: Only click the "ArcGIS Group" item in the list immediately to the right of the 
           "ArcGIS" item. **_DO NOT_** click on the larger "ArcGIS Group" link that appears in the wider space in the 
           rightmost part of the dialog box.)
    1. At the bottom right corner of the dialog box, click the "Import" button.
    1. In the alert box with the message "Import outcome 'ArcGIS Group' to group '_your course name here_'?", click the
       "OK" button.
    1. After the import is complete, you will see "ArcGIS Group" in your course's list of outcomes.
1. Each of your course's assignments which are to be synchronized with ArcGIS Online needs to include the "ArcGIS Group"
   outcome in their rubrics. **_You will need to do this for each new assignment you add to the course._** This can be
   simplified somewhat by adding the "ArcGIS Group" outcome to a single rubric that will be used by multiple 
   assignments. Each assignment that uses that rubric will automatically include the "ArcGIS Group" outcome. It's 
   recommended that rubrics should be given meaningful names. For example, a good name could be "_your course name 
   here_ Rubric (with ArcGIS sync)".
    1. Click on the name of an assignment in the list of your course's assignments.
    1. Edit the assignment's rubric (or add a new rubric if one doesn't already exist).
    1. Click on "🔍 Find Outcome".
    1. In the dialog box of your course's outcomes that appears, click "ArcGIS Group" in the list on the left side of 
       the box. (Note: **_DO NOT_** click on the larger "ArcGIS Group" link that appears in the wider space to the right
       of the list.)
    1. At the bottom right corner of the dialog box, click the "Import" button.
    1. In the alert box with the message "Import outcome 'ArcGIS Group' to group '_your course name here_'?", click the
       "OK" button.
    1. After the import is complete, you will see "ArcGIS Group" as part of the assignment's rubric.
    1. Finally, click the "Update Rubric" button (or the "Create Rubric" button if you were adding a new rubric).
1. Control the synchronization of your assignment with ArcGIS online by setting the "Available From", "Until", and 
   "Due Date" times.
   
Once all of the above requirements are satisfied, kartograafr will synchronize your course's assignments with ArcGIS
Online. It will happen automatically, several times each day.

### For Administrators and Developers

To set up the application, users will need to perform configuration steps in the Canvas and ArcGIS instances that they
want to connect, and specify environment variables to connect to those instances and determine other application
settings. The following sections provide instructions for how to complete this configuration. (Note: UM-affiliated 
users should contact Teaching & Learning, as much of this configuration is already in place.)

#### Canvas

Within your instance of Canvas, do the following:

1. Create an API access token.
1. Record the base URL of the Canvas API.
1. Create an outcome for ArcGIS and record its ID number.
1. Create a kartograafr configuration course and record its ID number.
    1. Within the new configuration course, create a page named `course-ids`.
    1. Add to the page the URLs of courses to be processed (they will appear as links on the page).
    1. Give support staff the permissions necessary to update that page (add them with the "Teacher" role).

#### ArcGIS

Within your instance of ArcGIS, do the following:

1. Record the organization name in use (e.g., at UM, `devumich` or `umich`)
1. Create a user with permission to create and modify user groups, and record the username and password.

### Application

For the application to run, environment variables need to be made available through a JSON file named **env.json** 
(or similar). This file provides key-value pairs that help the application access necessary accounts, find Canvas 
entities, and send emails. The application imports this file and uses its values to round out a few configuration 
classes defined in `config.py` (see the Installation section below for how to embed this file in the application). 

The `env.json` file contains sensitive information, including account login information and an API secret, and thus 
needs to be kept out of source control. Teaching & Learning maintains production, test, and local development versions 
of these files outside of GitHub. A template JSON file called `env_blank.json` has been provided as a starting point.

To create your version of this file, do the following:

1. Copy `env_blank.json`.
1. Rename the file `env.json` (for use in local development) or `[some name].json` (for use in OpenShift).
1. Replace the empty strings and 0's with the desired settings and values.

The meaning of each key and its expected value are described in the table below.

**Key** | **Description**
----- | -----
`Logging_Level` | The minimum level for log messages that will appear in output. We recommend either `INFO` or `DEBUG` for most use cases; see [Python's logging module](https://docs.python.org/3/library/logging.html) for more info.
`Logging_Directory` | The path where log files will be written; in OpenShift, this needs to be the `tmp` directory of the container's file system.
`SMTP_Server` | The name of the server emails should be sent from, if the `--email` flag is in use.
`Email_Sender_Address` | The name and email address to use in the FROM header of emails sent. This should take the form of "\"Severus Snape"\ <halfbloodprince@umich.edu>" (make sure to escape double quotes).
`Canvas_Base_URL` | The URL of the Canvas instance you want to pull Canvas data from; for production at UM, this is `umich.instructure.com`.
`Canvas_API_Token` | The API token to use when making requests for data related to courses, assignments, and users.
`Canvas_Config_Course_ID` | The ID number of the configuration course, (see the **Canvas** configuration section above).
`ArcGIS_Org_Name` | The name of the ArcGIS organization in use.
`ArcGIS_Username` | The name of an arcGIS user with permission for creating and modifying user groups.
`ArcGIS_Passowrd` | The name of the password for the username provided above.

----------------

## <a name='installationAndDevelopment'></a>Installation & Development

The sections below provide instructions for installing and running the application in various environments. Before
attempting to install or deploy, ensure the configuration steps under **For Administrators and Developers** have been
completed. Depending on the environment you plan to run the application in, you may also need to install some or all
of the following:
   * Python
   * Git
   * Docker Desktop
   * OpenShift CLI

### Local Development

To set up the application for use locally or in preparation for development work, do the following:

1. Clone the repository, and navigate into the repository.
   ```
   https://github.com/tl-its-umich-edu/kartograafr.git  # HTTPS
   git@github.com:tl-its-umich-edu/kartograafr.git  # SSH
   
   cd kartograafr
   ```
1. Create a virtual environment using `virtualenv`.
   ```
   virtualenv venv
   source venv/bin/activate  # for Mac OS
   ```
1. Install the dependencies in `requirements.txt`.
   ```
   pip install -r requirements.txt
   ```
1. Install the `arcgis` package separately.
   ```
   pip install arcgis --no-deps
   ```
1. Place the `env.json` file previously created in the `configuration/secrets/` directory.

1. Run the application.
   ```
   python main.py
   ```

#### Sending Email

To send emails with kartograafr, the `main.py` files needs to be executed using the `--email` flag, but configuring
the application to send email from a local environment requires additional steps. To assist in testing email
functionality, a Shell script called `runDebugEmail.sh` has been provided that creates a mock email server. To run
kartograafr with this mock server, do the following:

1. Ensure the `SMTP_Server` value in `env.json` is set to `localhost:1025`.
1. Execute the Shell script to start the server.
   ```
   /bin/bash runDebugEmail.sh
   ```
1. In a separate shell, terminal, or console window, run `main.py`.
   ```
   python main.py --email
   ```
The email will appear in the window where you ran the Shell script.

Alternatively, you can print the email content as part of application's output (without using the mock server) by 
passing the `--printEmail` flag when executing `main.py`.
```
python main.py --email --printEmail
```

### Docker

When developing locally, you can also run the application by leveraging the `Dockerfile` and Docker Desktop. To run
with Docker, do the following:

1. Build an image.
   ```
   docker build -t kartograafr .
   ```
2. Run a container using the tagged image.
   ```
   docker run kartograafr
   ```

Note: Currently, there is no way to test sending emails using Docker on a local machine.

### OpenShift

Running the application as a job using OpenShift and Jenkins involves several steps, which are beyond the scope of this 
README. However, it seems appropriate to explain some configuration steps assumed by the `Dockerfile` and unique to this
application.

* The `env.json` file described during the Configuration steps needs to be made available to running kartograafr 
  containers via an OpenShift ConfigMap, a type of Resource. A volume containing the ConfigMap should be mapped to the 
  `configuration/secrets` subdirectory. These details will be specified a configuration file (.yaml) defining the 
  pod.

* By default, the application will run without sending email and with the assumption that the JSON file will be named 
  `env.json`. However, the `start.sh` invoked by the `Dockerfile` and `config.py` will also check whether the 
  environment variables `ENV_FILE` and `SEND_EMAIL` have been defined. These can be set using the pod configuration 
  file. To use a different name for the JSON file, set `ENV_FILE` to a path beginning with `configuration/secrets/`
  and ending with the file name. To have the application send email, set `SEND_EMAIL` to the string `"True"`. The `env`
  block in the `.yaml` will look something like the following:

  ```
  - env:
     - name: ENV_FILE
       value: /configuration/secrets/env_test.json
     - name: SEND_EMAIL
       value: "True"
  ```