##### Run kartograafr in Docker.
### TTD (Things To Do)
# - a couple of settings should be overrideable by environment variables.  See TODOs below.
# - This runs as root.  Cron may require further work if the root user is not allowed.

FROM docker.io/python:2.7

RUN apt-get update && apt-get install -y cron vim

######### set timezone
# TODO: allow overriding the time zone setting with an environment variable.
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
#########

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/local/apps/kartograafr
RUN mkdir -p -v /var/log/kartograafr
RUN mkdir -p -v /var/log/kartograafr/courses

# The cron entry and config.py setup are done in startup-cron-env.sh.
# There may be a better way.

# Run setup container and then run cron
CMD ["/bin/bash","/usr/local/apps/kartograafr/startup-cron-env.sh"]

#end
