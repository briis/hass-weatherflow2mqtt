FROM python:3
LABEL org.opencontainers.image.source="https://github.com/briis/hass-weatherflow2mqtt"
RUN pip install paho-mqtt asyncio pyyaml sockets
RUN mkdir /app
WORKDIR /app
ADD __init__.py /app
ADD aioudp.py /app
ADD const.py /app
ADD weatherflow_mqtt.py /app
ADD helpers.py /app
ENV TZ=Europe/Copenhagen
EXPOSE 50222/udp
EXPOSE 1883
CMD [ "python", "weatherflow_mqtt.py" ]