# Build Container

If you don't want to use the pre-build container, you can build it your self, by cloning this Project.

1. Place yourself in the same directory as the `Dockerfile` file and issue the following command:
  `docker build -t weatherflow2mqtt .`
2. Run the Program

   Create the container with the following command:

   - `docker create --name weatherflow2mqtt -e TZ=YOUR_TIMEZONE -v $(pwd):/usr/local/config -p 0.0.0.0:50222:50222/udp weatherflow2mqtt`
   - `docker start weatherflow2mqtt`
