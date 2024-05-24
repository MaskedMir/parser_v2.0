FROM python:3.12

ARG DOCKER_APP_PATH

WORKDIR $DOCKER_APP_PATH

COPY requirements.txt .
COPY main.py .
COPY config.py .

RUN mkdir -p ./base_parser
COPY base_parser ./base_parser
RUN mkdir -p ./database
COPY database ./database
RUN mkdir -p ./hh_parser
COPY hh_parser ./hh_parser
RUN mkdir -p ./shared
COPY shared ./shared
RUN mkdir -p ./tadv_parser
COPY tadv_parser ./tadv_parser
RUN mkdir -p ./templates
COPY templates ./templates

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config default-libmysqlclient-dev build-essential python3-dev bash

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "main.py"]