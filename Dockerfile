FROM python:3.9-slim-buster
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"

RUN mkdir -p /data
RUN mkdir -p /src/weatherflow2mqtt
WORKDIR /src/weatherflow2mqtt
ADD requirements.txt test_requirements.txt /src/weatherflow2mqtt/
RUN apt-get update && \
    apt-get -y install build-essential
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ADD setup.py /src/weatherflow2mqtt/
ADD translations /src/weatherflow2mqtt/translations/

ADD weatherflow2mqtt /src/weatherflow2mqtt/weatherflow2mqtt/
RUN python setup.py install


ENV TZ=Europe/Copenhagen

EXPOSE 50222/udp
EXPOSE 1883

CMD [ "weatherflow2mqtt" ]
