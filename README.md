![MerossToInfluxDB](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmQ5NWZjeW9ja3I4anRoaHEzcjh2b3o2NGoyc2E5OXk5d3lhaTI3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/9ADoZQgs0tyww/giphy.gif)
# MerossToInfluxDB

MerossToInfluxDB is a Python project that enables the collection of electricity usage data from Meross smart devices and stores it in an InfluxDB database. This project is particularly useful for monitoring the energy consumption of specific devices in your home or office. The [connector.py](connector.py) script is designed to be run in the background and pushes every 20 seconds to influxdb the power metrics of the power plugs you choose. 

## Features

- **Device Discovery:** Automatically discovers Meross devices that are capable of electricity measurement.
- **Data Extraction:** Retrieves real-time electricity consumption data (power, voltage, and current) from the selected Meross devices.
- **Data Storage:** Efficiently stores the extracted data in an InfluxDB database for further analysis and visualization.
- **Customizable Fetch Interval:** Allows setting a custom interval for data fetching.

## Requirements

- Python 3.x
- Access to Meross devices capable of electricity measurement.
- An InfluxDB server (either local or remote) to store the data.

## Testing your meross setup & get device overview
In order to test the meross setup and see all devices that are currently available, the script [deviceinfo.py](deviceinfo.py) is included in this repository. After filling out the [credentials.txt](credentials.txt.example) file with your credentials and removing the .example file ending, run the device info script once to get an overview over all avaiable devices. For each device you want to write the data to InfluxDB, please fill the exact names into line 31 in [connector.py](connector.py).

## Installation Instructions

1. **Set Up Python Environment:**
   - Ensure Python 3.x is installed on your system.
   - It's recommended to use a virtual environment:
     ```bash
     python -m venv meross-env
     source meross-env/bin/activate  # On Windows, use `meross-env\Scripts\activate`
     ```

2. **Install Dependencies:**
   - Navigate to the project directory.
   - Install required Python packages using:
     ```bash
     pip install -r requirements.txt
     ```

3. **Configuration:**
   - Create a `credentials.txt` file in the project directory with the following content, filling in your own details (see [credentials.txt.example](credentials.txt.example)):
     ```
     MEROSS_EMAIL=your_meross_account_email
     MEROSS_PASSWORD=your_meross_account_password
     INFLUXDB_URL=your_influxdb_url
     INFLUXDB_TOKEN=your_influxdb_token
     INFLUXDB_ORG=your_influxdb_org
     INFLUXDB_BUCKET=your_influxdb_bucket
     API_BASE_URL=api_base_region
     ```
    There are the following API Base regions, the one fitting your location:
    1. Asia-Pacific: "iotx-ap.meross.com"
    2. Europe: "iotx-eu.meross.com"
    3. US: "iotx-us.meross.com"

   - If not done yet: **Fill out the device names that you got by running [deviceinfo.py](deviceinfo.py) into line 31 in [connector.py](connector.py).**

4. **Running the Script:**
   - Run the script using:
     ```bash
     python script_name.py
     ```
     Replace `connector.py` with the actual name of the Python script.

5. **Monitoring:**
   - The script will continuously monitor the specified Meross devices and log data to your InfluxDB database at the set interval.

## Usage

- Before running the script, ensure that the Meross devices you want to monitor are set up and connected to your network.
- Edit the `device_names_to_monitor` list in the script to include the names of the Meross devices you wish to monitor.
- Set the `fetch_interval` in the script to control how often data is fetched from the devices.
- The script will output the current readings to the console and write the data to the specified InfluxDB bucket.

## Notes

- This project requires an active internet connection for the Meross API to function.
- Ensure your InfluxDB instance is properly set up and accessible from the script.
- Handle your credentials securely and avoid exposing them in public or unsecured files.

## Troubleshooting

- If you encounter issues with device discovery, ensure your devices are correctly set up with the Meross app and are online.
- For any connection issues with InfluxDB, verify your InfluxDB URL, token, organization, and bucket details.
- Check your Python environment and dependencies if you encounter any script execution errors.