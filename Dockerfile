FROM python:3
RUN pip install paho-mqtt asyncio pyyaml
RUN mkdir /app
ADD __init__.py /app
ADD aioudp.py /app
ADD const.py /app
ADD weatherflow_mqtt.py /app
ADD helpers.py /app
ENV TZ=Europe/Copenhagen
EXPOSE 50222/udp
EXPOSE 1883
CMD [ "python", "./app/weatherflow_mqtt.py" ]