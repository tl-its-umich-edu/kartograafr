##### Run kartograafr in Docker.
### TTD (Things To Do)
# - a couple of settings should be overrideable by environment variables.  See TODOs below.
# - This runs as root.  Cron may require further work if the root user is not allowed.

FROM python:2.7

RUN apt-get update && apt-get install -y cron

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

# Add the cron entry for kartograafr
## TODO: make the specific cron source file settable depending on environment variable.
RUN cat /usr/local/apps/kartograafr/rootdir_etc_cron.d/kartograafr.dev >> /etc/cron.d/kartograafr
RUN crontab /etc/cron.d/kartograafr

# Run cron.
CMD ["cron", "-f"]

#end
