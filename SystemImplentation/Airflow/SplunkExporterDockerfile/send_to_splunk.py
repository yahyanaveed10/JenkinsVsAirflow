import csv
import os
import requests
import json

splunk_url = 'https://<splunk_instance>:8088/services/collector'
token = '<token>'

pvc_mount_path = "/app/random"    #os.getenv('PVC_MOUNT_PATH', '/mnt/data')


def is_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False

# Function to convert CSV data to JSON
def csv_to_json(file_path):
    with open(file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        data = [row for row in reader]
    return data

# Traverse through directories and read files recursively
print("I am in the python script")

#print(f"PVC mount path: {a}")

# Traverse through directories and read files recursively
for root, dirs, files in os.walk(pvc_mount_path):
    print(f"Inspecting directory: {root}")
    for file_name in files:
        file_path = os.path.join(root, file_name)
        print(f"Processing file: {file_path}")

        # Read data from each file
        try:
            if file_name.endswith('.csv'):
                # Convert CSV to JSON
                event_data = csv_to_json(file_path)
                sourcetype = "csv_data"  # Customize sourcetype for CSV files
                print(f"{file_path} contains CSV data")
            else:
                # Read file content as text
                with open(file_path, 'r') as file:
                    data = file.read()
                    print(f"Read data from {file_path}")

                # Determine if the file content is JSON or something else
                if is_json(data):
                    event_data = json.loads(data)  # Send as JSON event
                    sourcetype = "json_data"  # Customize the sourcetype for JSON files
                    print(f"{file_path} contains JSON data")
                else:
                    event_data = data  # Send as plain text or other format
                    sourcetype = "plain_text"  # Customize the sourcetype for non-JSON files
                    print(f"{file_path} contains plain text or other data")

            # Prepare payload for Splunk
            payload = {
                "event": event_data,
                "sourcetype": sourcetype,
                "index": "airflow_analysis"
            }

            headers = {
                'Authorization': f'Splunk {token}',
                'Content-Type': 'application/json'
            }

            # Send data to Splunk
            response = requests.post(splunk_url, data=json.dumps(payload), headers=headers,verify=False)

            # Check for success
            if response.status_code == 200:
                print(f"Data from {file_path} sent to Splunk successfully!")
            else:
                print(f"Failed to send data from {file_path} to Splunk: {response.status_code}, {response.text}")

        except Exception as e:
            print(f"Error reading or sending file {file_path}: {str(e)}")