FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /MasarykBOT
COPY . /MasarykBOT

RUN apt-get update && apt-get install -y git
RUN apt-get install -y --no-install-recommends dvipng texlive-latex-extra texlive-fonts-recommended cm-super

RUN pip install --upgrade pip
RUN pip install -r bot/requirements.txt
RUN pip install -r tests/requirements.txt
RUN pip install mypy>=0.990
RUN pip install flake8>=4.0.1
RUN pip install coverage>=6.3.2