##FROM mcr.microsoft.com/playwright/python:v1.37.0-jammy
#
##ARG DOCKER_APP_PATH
##
##WORKDIR $DOCKER_APP_PATH
#FROM python:3.12
#
#WORKDIR /app
#
#ADD . /app
#
#COPY requirements.txt .
#COPY main.py .
#COPY config.py .
#
#
#
##RUN apt-get update && apt-get install -y --no-install-recommends \
##        pkg-config libmysqlclient-dev build-essential python3-dev bash
#
#RUN pip install --no-cache-dir -r requirements.txt
#
#CMD ["python", "-u", "main.py"]
FROM python:3.12

WORKDIR /app

ADD . /app
#RUN pip install --only-binary :all: greenlet
#RUN pip install --only-binary :all: Flask-SQLAlchemy
#RUN pip install peewee
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --only-binary :all: -r requirements.txt

CMD ["python", "-u",  "./project/main.py"]
