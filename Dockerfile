FROM python:3.13-slim

COPY requirements.txt /requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install -r requirements.txt

# ArcGIS must be installed separately because some of its dependencies cause
# conflicts, but we don't need those dependencies.  We cannot use the
# `--no-deps` flag in `requirements.txt`, so we install ArcGIS separately.
RUN pip install arcgis==1.9.0 --no-deps

WORKDIR /kartograafr/
COPY . /kartograafr/

# Set the local time zone of the Docker image
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["/bin/bash", "start.sh"]

# Done!
