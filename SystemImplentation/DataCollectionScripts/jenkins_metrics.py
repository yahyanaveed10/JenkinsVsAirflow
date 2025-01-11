import time

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import psycopg2

# Jenkins credentials and URL
JENKINS_URL = "<jenkins>"
USERNAME = '<user>'
API_TOKEN = '<pass>'
auth = HTTPBasicAuth(USERNAME, API_TOKEN)

# PostgreSQL connection parameters
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "metrics_db"
PG_USER = "your_user"
PG_PASS = "your_password"

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DB,
    user=PG_USER,
    password=PG_PASS
)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS jenkins_builds (
    job_name TEXT,
    build_number INTEGER PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_queue_time_seconds FLOAT,
    total_duration_seconds FLOAT,
    run_duration_without_queue FLOAT, 
    build_status TEXT
)
""")
conn.commit()

def fetch_jobs():
    response = requests.get(f"{JENKINS_URL}/job/Test_JenkinsVsAirflow/api/json?tree=jobs[name]", auth=auth)
    response.raise_for_status()
    return [job['name'] for job in response.json().get('jobs', [])]

def fetch_builds(job_name):
    response = requests.get(f"{JENKINS_URL}/job/Test_JenkinsVsAirflow/job/{job_name}/api/json", auth=auth)
    response.raise_for_status()
    return response.json().get('builds', [])

def fetch_build_details(job_name, build_number):
    response = requests.get(f"{JENKINS_URL}/job/Test_JenkinsVsAirflow/job/{job_name}/{build_number}/api/json", auth=auth)
    response.raise_for_status()
    return response.json()

def inspect_jenkins_jobs():
    for job_name in fetch_jobs():
        for build in fetch_builds(job_name):
            build_number = build['number']
            build_details = fetch_build_details(job_name, build_number)

            # Get start time and duration details
            start_time = datetime.fromtimestamp(build_details['timestamp'] / 1000)
            duration_seconds = build_details.get('duration', 0) / 1000
            end_time = start_time + timedelta(seconds=duration_seconds)

            # Queue time details
            queue_action = next((action for action in build_details['actions']
                               if '_class' in action and action['_class'] == 'jenkins.metrics.impl.TimeInQueueAction'), None)
            total_queue_time = (queue_action.get('buildableTimeMillis', 0) / 1000) if queue_action else 0

            # Calculate run duration without queue
            run_duration_without_queue = (
                duration_seconds - total_queue_time if total_queue_time > 0
                else duration_seconds
            )

            # Fetch build status
            build_status = build_details.get('result', 'UNKNOWN')

            # Insert data with new column
            cursor.execute("""
                INSERT INTO jenkins_builds (
                    job_name, build_number, start_time, end_time, 
                    total_queue_time_seconds, total_duration_seconds, 
                    run_duration_without_queue, build_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                job_name, build_number, start_time, end_time,
                total_queue_time, duration_seconds,
                run_duration_without_queue, build_status
            ))
            conn.commit()

            print(f"Inserted Job: {job_name}, Build: {build_number}, "
                  f"Start Time: {start_time}, End Time: {end_time}, "
                  f"Queue Time: {total_queue_time} seconds, "
                  f"Duration: {duration_seconds} seconds, "
                  f"Run Duration Without Queue: {run_duration_without_queue} seconds, "
                  f"Status: {build_status}")
def main():
    inspect_jenkins_jobs()
    #cursor.close()
    #conn.close()

if __name__ == "__main__":
    #x = 0
   # while x < 20:
       main()
       time.sleep(600)
       #x += 1
