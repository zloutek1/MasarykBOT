FROM python:3.8.2-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /MasarykBOT
COPY . /MasarykBOT
WORKDIR /MasarykBOT

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "./__main__.py"]
