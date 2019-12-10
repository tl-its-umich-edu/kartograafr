# Use a Python base image
FROM python:3.7

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# arcgis needs to be installed separately because of issues when including the requirement with a flag in
# requirements.txt
RUN pip install arcgis --no-deps

WORKDIR /kartograafr/
COPY . /kartograafr/

# Set up log file directories
RUN mkdir -p -v /tmp/log/kartograafr/courses

# Set the local time zone of the Docker image
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["/bin/bash", "start.sh"]

# Done!
