import asyncio
import os

from meross_iot.controller.mixins.electricity import ElectricityMixin
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

def load_credentials(filename):
    credentials = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split('=')
                key = parts[0]
                value = '='.join(parts[1:])  # This handles the case where the value contains '='
                credentials[key] = value
    except FileNotFoundError:
        print(f"Using system environment variables.")
        return {}
    return credentials

credentials = load_credentials('config.env')
EMAIL = credentials['MEROSS_EMAIL']
PASSWORD = credentials['MEROSS_PASSWORD']


async def main():
    # Setup the HTTP client API from user-password
    http_api_client = await MerossHttpClient.async_from_user_password(api_base_url='iotx-eu.meross.com', email=EMAIL, password=PASSWORD)

    # Setup and start the device manager
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()

    # Retrieve all the devices that implement the electricity mixin
    await manager.async_device_discovery()
    devs = manager.find_devices(device_class=ElectricityMixin)

    if len(devs) < 1:
        print("No electricity-capable device found...")
    else:
        for index, dev in enumerate(devs):
            # Update device status: this is needed only the very first time we play with this device (or if the
            # connection goes down)
            await dev.async_update()

            # Read the electricity power/voltage/current
            instant_consumption = await dev.async_get_instant_metrics()
            print(f"Current consumption data of {dev.name} (device number {index}) that is {dev.online_status}: {instant_consumption}")


    # Close the manager and logout from http_api
    manager.close()
    await http_api_client.async_logout()

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.stop()
