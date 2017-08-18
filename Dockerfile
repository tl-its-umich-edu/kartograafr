FROM python:2.7

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/local/apps/kartograafr
RUN mkdir -p -v  /var/log/kartograafr
RUN mkdir -p -v /var/log/kartograafr/courses

#RUN ls -l /var/log/kartograafr/courses
#RUN ls -l /var/log/kartograafr/courses/*

# run without trying to mail logs.
#CMD [ "python", "/usr/local/apps/kartograafr/main.py" ]
#CMD [ "python", "/usr/local/apps/kartograafr/main.py","--mail"]
CMD ["bash"]
#end
