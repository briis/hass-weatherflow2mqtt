# Build Container

1. Place yourself in the same directory as the `Dockerfile` file and issue the following command:
  `docker build -t weatherflow2mqtt .`

# Run Container

Create the container with the following command:

- `docker create --name weatherflow2mqtt -v /Users/bjarne/udvikling/weatherflowmqtt:/config -p 50222:50222/udp weatherflow2mqtt`
- `docker start weatherflow2mqtt`
