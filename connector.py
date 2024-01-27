import asyncio
import os
import re
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

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

credentials = load_credentials('credentials.txt')
EMAIL = os.environ.get('MEROSS_EMAIL') or credentials['MEROSS_EMAIL']
PASSWORD = os.environ.get('MEROSS_PASSWORD') or credentials['MEROSS_PASSWORD']
INFLUXDB_URL = os.environ.get('INFLUXDB_URL') or credentials['INFLUXDB_URL']
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN') or credentials['INFLUXDB_TOKEN']
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG') or credentials['INFLUXDB_ORG']
INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET') or credentials['INFLUXDB_BUCKET']
API_BASE_URL = os.environ.get('API_BASE_URL') or credentials['API_BASE_URL']

# List of device names to monitor
device_names_to_monitor = ['PowerPlug1', 'PowerPlug2']

async def main(fetch_interval):
    http_api_client = await MerossHttpClient.async_from_user_password(api_base_url=API_BASE_URL, email=EMAIL, password=PASSWORD)
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()
    await manager.async_device_discovery()

    influxdb_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    try:
        while True:
            devs = [dev for dev in manager.find_devices(device_class=ElectricityMixin) if dev.name in device_names_to_monitor]

            if len(devs) < 1:
                print("No device to monitor from given list found :(...")
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

                    print(f"Device: {dev.name} - Power: {power} W, Voltage: {voltage} V, Current: {current} A")

                    # Writing data to InfluxDB
                    point = Point("meross_data").tag("device", dev.name).field("power", power).field("voltage", voltage).field("current", current)
                    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

            await asyncio.sleep(fetch_interval)

    except KeyboardInterrupt:
        print("Interrupted by user, closing...")

    finally:
        manager.close()
        await http_api_client.async_logout()
        influxdb_client.close()

if __name__ == '__main__':
    fetch_interval = 20  # Set your desired interval in seconds
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(fetch_interval))
    loop.close()