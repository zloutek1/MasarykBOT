FROM python:3.9.1-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /MasarykBOT
COPY . /MasarykBOT

RUN apt-get update && apt-get install -y git

COPY bot/requirements.txt bot/requirements.txt
RUN pip install -r bot/requirements.txt
RUN pip install mypy==0.931
RUN pip install flake8==4.0.1
RUN pip install coverage==6.3.2