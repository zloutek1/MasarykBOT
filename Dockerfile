FROM python:3.8.2-slim

WORKDIR /MasarykBOT

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "./__main__.py"]
