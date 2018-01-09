##### Run kartograafr in Docker.

### TTD (Things To Do)
# - Pass in the CONFIG_TYPE from OpenShift environment variable.
# - allow passing in the debug level as well.

# - This container runs as root.  Cron may require further work if the root user is not allowed.

# Need to build in anaconda environment
FROM continuumio/anaconda3

RUN apt-get update && apt-get install -y cron vim

######### set timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
#########

# Create a new conda environment and then install arcgis python sdk in that environment.
RUN conda create --name py35 python=3.5
RUN /bin/bash -c "source activate py35 && conda install -c esri arcgis -y"

WORKDIR /usr/src/app

COPY requirements.txt ./
# Do the pip install in chosen conda environment
RUN /bin/bash -c "source activate py35 && pip install --no-cache-dir -r requirements.txt"

COPY . /usr/local/apps/kartograafr
RUN mkdir -p -v /var/log/kartograafr
RUN mkdir -p -v /var/log/kartograafr/courses

WORKDIR /usr/local/apps/kartograafr

# The script is run by cron.  The final crontab and configuration files
# are installed at startup time in the startup-cron-env script so that
# a single build can be used in multiple environment.

# Run setup container and then run cron
CMD ["/bin/bash","/usr/local/apps/kartograafr/startup-cron-env.sh"]

#end
