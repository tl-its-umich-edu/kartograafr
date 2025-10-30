FROM python:3.13-slim

COPY requirements.txt /requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /kartograafr/
COPY . /kartograafr/

# Set the local time zone of the Docker image
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["/bin/bash", "start.sh"]
