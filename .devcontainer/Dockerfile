FROM python:3.9.1-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /MasarykBOT
COPY . /MasarykBOT

RUN apt-get update && apt-get install -y git

COPY bot/requirements.txt bot/requirements.txt
RUN pip install -r bot/requirements.txt
RUN pip install mypy==0.812
RUN pip install flake8==3.8.4
RUN pip install coverage==5.5