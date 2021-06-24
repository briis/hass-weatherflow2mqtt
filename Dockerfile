FROM python:3
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"
ADD VERSION .
RUN pip install paho-mqtt asyncio aiohttp pyyaml
RUN mkdir -p /usr/local/config
RUN mkdir /app
RUN mkdir /app/translations
WORKDIR /app
ADD __init__.py /app
ADD aioudp.py /app
ADD const.py /app
ADD forecast.py /app
ADD weatherflow_mqtt.py /app
ADD helpers.py /app
ADD sqlite.py /app
ADD translations/en.json /app/translations
ADD translations/da.json /app/translations
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
CMD [ "python", "weatherflow_mqtt.py" ]