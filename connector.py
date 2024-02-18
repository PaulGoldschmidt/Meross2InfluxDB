import asyncio
import os
import re
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from meross_iot.controller.mixins.electricity import ElectricityMixin
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

def load_config(filename):
    configs = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split('=')
                key = parts[0]
                value = '='.join(parts[1:])  # This handles the case where the value contains '='
                configs[key] = value
    except FileNotFoundError:
        print(f"Using system environment variables.")
        return {}
    return configs

config = load_config('config.env')
EMAIL = os.environ.get('MEROSS_EMAIL') or config['MEROSS_EMAIL']
PASSWORD = os.environ.get('MEROSS_PASSWORD') or config['MEROSS_PASSWORD']
INFLUXDB_URL = os.environ.get('INFLUXDB_URL') or config['INFLUXDB_URL']
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN') or config['INFLUXDB_TOKEN']
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG') or config['INFLUXDB_ORG']
INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET') or config['INFLUXDB_BUCKET']
API_BASE_URL = os.environ.get('API_BASE_URL') or config['API_BASE_URL']
FETCH_INTERVAL = os.environ.get('FETCH_INTERVAL') or config['FETCH_INTERVAL']
DEBUG = os.environ.get('DEBUG') or config['DEBUG']

# List of device names to monitor
device_names_env = os.environ.get('DEVICE_NAMES_TO_MONITOR')
device_names_to_monitor = device_names_env.split(',') if device_names_env else config['DEVICE_NAMES_TO_MONITOR'].split(',')

async def main(FETCH_INTERVAL):
    http_api_client = await MerossHttpClient.async_from_user_password(api_base_url=API_BASE_URL, email=EMAIL, password=PASSWORD)
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()
    await manager.async_device_discovery()

    influxdb_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    try:
        while True:
            if 'ALL' in str(device_names_to_monitor):
                devs = manager.find_devices(device_class=ElectricityMixin)
            else: #If all devices shell be monitored
                devs = [dev for dev in manager.find_devices(device_class=ElectricityMixin) if dev.name in device_names_to_monitor]

            if len(devs) < 1:
                if DEBUG: print("No device to monitor from given list (" + str(device_names_to_monitor) + ") found :(...")
            else:
                for index, dev in enumerate(devs):
                    await dev.async_update()
                    instant_consumption = await dev.async_get_instant_metrics()

                    # Extracting power, voltage, and current
                    power_search = re.search(r'POWER = (\d+\.\d+) W', str(instant_consumption))
                    voltage_search = re.search(r'VOLTAGE = (\d+\.\d+) V', str(instant_consumption))
                    current_search = re.search(r'CURRENT = (\d+\.\d+) A', str(instant_consumption))

                    power = float(power_search.group(1)) if power_search else None
                    voltage = float(voltage_search.group(1)) if voltage_search else None
                    current = float(current_search.group(1)) if current_search else None

                    # Writing data to InfluxDB
                    point = Point("meross_data").tag("device", dev.name).field("power", power).field("voltage", voltage).field("current", current)
                    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
                    if DEBUG: print(f"Write to InfluxDB successful for device: {dev.name} with power: {power} W, Voltage: {voltage} V and Current: {current} A")

            await asyncio.sleep(FETCH_INTERVAL)

    except KeyboardInterrupt:
        print("Interrupted by user, closing...")

    finally:
        manager.close()
        await http_api_client.async_logout()
        influxdb_client.close()

if __name__ == '__main__':
    print("##############################################")
    print("Starting MerossToInfluxDB by p3g3, Version 2.2")
    print("##############################################")
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(int(FETCH_INTERVAL)))
    loop.close()
