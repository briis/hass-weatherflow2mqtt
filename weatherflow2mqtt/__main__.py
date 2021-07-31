"""Main module."""
import asyncio

from weatherflow2mqtt import weatherflow_mqtt


def main():
    """Start Main Program."""
    try:
        asyncio.run(weatherflow_mqtt.main())
    except KeyboardInterrupt:
        print("\nExiting Program")


if __name__ == "__main__":
    main()
