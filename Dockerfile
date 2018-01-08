##### Run kartograafr in Docker.
##### Note that the crontab type is hard coded.  Currently it defaults to the dev version.
##### The production build should come from a branch where the copy line in the docker file
##### has been updated to the production version.
### TTD (Things To Do)
# - a couple of settings should be overrideable by environment variables.  See TODOs below.
# - This runs as root.  Cron may require further work if the root user is not allowed.

# Need to build in anaconda environment
FROM continuumio/anaconda3

RUN apt-get update && apt-get install -y cron vim

######### set timezone
# TODO: allow overriding the time zone setting with an environment variable.
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
#########

# Create a new conda environment and then install in that environment.
RUN conda create --name py35 python=3.5
RUN /bin/bash -c "source activate py35 && conda install -c esri arcgis -y"

WORKDIR /usr/src/app

COPY requirements.txt ./
# install in chosen conda environment
RUN /bin/bash -c "source activate py35 && pip install --no-cache-dir -r requirements.txt"

COPY . /usr/local/apps/kartograafr
RUN mkdir -p -v /var/log/kartograafr
RUN mkdir -p -v /var/log/kartograafr/courses

# Add the cron entry for kartograafr defaults to dev crontab

## TODO: make the specific cron source file settable depending on environment variable.
 RUN cat /usr/local/apps/kartograafr/rootdir_etc_cron.d/kartograafr.dev >> /etc/cron.d/kartograafr
#RUN cat /usr/local/apps/kartograafr/rootdir_etc_cron.d/kartograafr >> /etc/cron.d/kartograafr

RUN crontab /etc/cron.d/kartograafr

WORKDIR /usr/local/apps/kartograafr

# Run cron.
CMD ["cron", "-f"]

#end
