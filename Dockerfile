FROM python:3.9-slim-buster
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"

RUN mkdir -p /usr/local/config
RUN mkdir -p /src/weatherflow2mqtt
WORKDIR /src/weatherflow2mqtt
ADD requirements.txt test_requirements.txt /src/weatherflow2mqtt/
RUN pip install -r requirements.txt

ADD setup.py /src/weatherflow2mqtt/
ADD translations /src/weatherflow2mqtt/translations/

ADD weatherflow2mqtt /src/weatherflow2mqtt/weatherflow2mqtt/
RUN python setup.py install


ENV TZ=Europe/Copenhagen
ENV TEMPEST_DEVICE=True
ENV UNIT_SYSTEM=metric
ENV RAPID_WIND_INTERVAL=0
ENV DEBUG=False
ENV ELEVATION=0
ENV WF_HOST=0.0.0.0
ENV WF_PORT=50222
ENV MQTT_HOST=127.0.0.1
ENV MQTT_PORT=1883
ENV MQTT_USERNAME=
ENV MQTT_PASSWORD=
ENV MQTT_DEBUG=False
ENV ADD_FORECAST=False
ENV STATION_ID=
ENV STATION_TOKEN=
ENV FORECAST_INTERVAL=30
ENV LANGUAGE=en

EXPOSE 50222/udp
EXPOSE 1883

CMD [ "weatherflow2mqtt" ]
