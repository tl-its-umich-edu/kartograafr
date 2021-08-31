# Use a Python base image
FROM python:3.8-slim

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# arcgis needs to be installed separately because of issues when including the requirement with a flag in
# requirements.txt
RUN pip install arcgis==1.9.0 --no-deps

WORKDIR /kartograafr/
COPY . /kartograafr/

# Set the local time zone of the Docker image
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["/bin/bash", "start.sh"]

# Done!
