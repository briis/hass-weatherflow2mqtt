FROM python:3
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"
ADD VERSION .
RUN pip install paho-mqtt asyncio pyyaml
RUN mkdir -p /usr/local/config
RUN mkdir /app
WORKDIR /app
ADD __init__.py /app
ADD aioudp.py /app
ADD const.py /app
ADD weatherflow_mqtt.py /app
ADD helpers.py /app
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
EXPOSE 50222/udp
EXPOSE 1883
CMD [ "python", "weatherflow_mqtt.py" ]