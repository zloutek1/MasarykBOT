FROM python:3.7.6-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -y --no-install-recommends \
    install tzdata=2020a-0+deb10u1 graphviz=2.40.1-6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Europe/Prague

VOLUME /MasarykBOT
WORKDIR /MasarykBOT

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .