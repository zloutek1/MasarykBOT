FROM python:3.7-slim-buster
WORKDIR /bot
COPY requirements.txt requirements.txt
RUN python -m pip install -U -r requirements.txt
COPY . .
COPY config-docker.py config.py
CMD ["python", "-u", "__main__.py"]
