import os
import asyncio
from influxdb_client import InfluxDBClient
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

# Load credentials from a file or environment variables
def load_credentials(filename):
    credentials = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split('=')
                key = parts[0]
                value = '='.join(parts[1:])
                credentials[key] = value
    except FileNotFoundError:
        print(f"Using system environment variables.")
        return {}
    return credentials

credentials = load_credentials('config.env')
EMAIL = os.environ.get('MEROSS_EMAIL') or credentials['MEROSS_EMAIL']
PASSWORD = os.environ.get('MEROSS_PASSWORD') or credentials['MEROSS_PASSWORD']
INFLUXDB_URL = os.environ.get('INFLUXDB_URL') or credentials['INFLUXDB_URL']
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN') or credentials['INFLUXDB_TOKEN']
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG') or credentials['INFLUXDB_ORG']
API_BASE_URL = os.environ.get('API_BASE_URL') or credentials['API_BASE_URL']

async def check_meross():
    try:
        http_client = await MerossHttpClient.async_from_user_password(api_base_url=API_BASE_URL, email=EMAIL, password=PASSWORD)
        manager = MerossManager(http_client=http_client)
        await manager.async_init()
        await manager.async_device_discovery()
        await asyncio.sleep(3) # wait three seconds to avoid "Task was destroyed but it is pending!" error
        manager.close()
        await http_client.async_logout()
        return True
    except Exception as e:
        print(f"Meross API check failed: {e}")
        return False

def check_influxdb():
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        client.close()
        return True
    except Exception as e:
        print(f"InfluxDB check failed: {e}")
        return False

async def main():
    meross_status = await check_meross()
    influxdb_status = check_influxdb()

    if meross_status and influxdb_status:
        print("Health check passed: Both InfluxDB and Meross API are operational.")
        return 0
    else:
        print("Health check failed.")
        return 1

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    status = loop.run_until_complete(main())
    loop.close()
    exit(status)
