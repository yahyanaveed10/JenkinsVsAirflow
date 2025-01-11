import requests
from datetime import datetime, timedelta

JENKINS_URL = "<Jenkins>"
auth = ('user', '<pass>')  # Use Jenkins credentials


# Fetch all jobs
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

            start_time = datetime.fromtimestamp(build_details['timestamp'] / 1000)  # Convert from milliseconds
            duration_seconds = build_details.get('duration', 0) / 1000  # Convert from milliseconds to seconds
            end_time = start_time + timedelta(seconds=duration_seconds)  # Create a timedelta
            #timestamp = build["timestamp"]
            #start_time = build["startTimeInMillis"]
           # queuing_duration = start_time - timestamp
           # print("Queuing duration: ", queuing_duration)
            #build_state = build_details.get('result', 'UNKNOWN')  # Default to UNKNOWN if result is not available

            queue_action = next((action for action in build_details['actions'] if '_class' in action and action['_class'] == 'jenkins.metrics.impl.TimeInQueueAction'), None)

            if queue_action:
               # total_queue_time = (
               #     queue_action.get('blockedDurationMillis', 0) +
               #     queue_action.get('buildableDurationMillis', 0) +
               #     queue_action.get('waitingDurationMillis', 0)
                #)
                 total_queue_time = queue_action.get('buildableTimeMillis')
            else:
                total_queue_time = 0

            total_duration_minutes = duration_seconds # / 60  # Convert total duration to minutes

            print(f"Job: {job_name}, Build: {build_number}, Start Time: {start_time}, End Time: {end_time}, Total Queue Time: {total_queue_time / 1000} seconds, Total Duration: {total_duration_minutes:.2f} seconds")
def fetch_queue_details(queue_id):
    try:
        response = requests.get(f"{JENKINS_URL}/queue/item/{queue_id}/api/json", auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching queue details for Queue ID {queue_id}: {e}")
        return None



def fetch_queue_items():
    response = requests.get(f"{JENKINS_URL}/queue/api/json", auth=auth)
    response.raise_for_status()
    return response.json().get('items', [])

def fetch_queue_item(queue_id):
    response = requests.get(f"{JENKINS_URL}/queue/item/{queue_id}/api/json", auth=auth)
    response.raise_for_status()
    return response.json()

def inspect_queue():
    queue_items = fetch_queue_items()

    for item in queue_items:
        queue_id = item['id']
        item_details = fetch_queue_item(queue_id)
        print(f"Queue ID: {queue_id}, Details: {item_details}")
def main():
    #inspect_queue()
    inspect_jenkins_jobs()

if __name__ == "__main__":
    main()