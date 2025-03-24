FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

RUN python3 -m pip install \
    flask \
    flask-cors \
    waitress

RUN mkdir -p /usr/src
RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY ./app.py .

EXPOSE 8080

CMD ["python3", "app.py"]
