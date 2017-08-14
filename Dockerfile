FROM python:2.7

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/local/apps/kartograafr
RUN mkdir /var/log/kartograafr

CMD [ "python", "/usr/local/apps/kartograafr/main.py" ]

#end
