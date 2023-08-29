FROM python:3.11-slim-buster
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"

RUN mkdir -p /data
WORKDIR /src/weatherflow2mqtt

ADD requirements.txt test_requirements.txt /src/weatherflow2mqtt/
ADD weatherflow2mqtt /src/weatherflow2mqtt/weatherflow2mqtt/
ADD setup.py /src/weatherflow2mqtt/

RUN apt-get update \
    && apt-get -y install build-essential \
    && pip install --upgrade --no-cache-dir pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python setup.py install \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*


ENV TZ=Europe/Copenhagen

EXPOSE 50222/udp
EXPOSE 1883

CMD [ "weatherflow2mqtt" ]
