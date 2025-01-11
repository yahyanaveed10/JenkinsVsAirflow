from datetime import datetime

import requests

AIRFLOW_API_URL = "https://<airflow_instance>/api/v1"
airflow_auth = ("user", "<pass>")


def fetch_dags():
    response = requests.get(f"{AIRFLOW_API_URL}/dags", auth=airflow_auth)
    response.raise_for_status()
    print("DAGS: ", response.json()['dags'])
    return response.json()['dags']


def fetch_dag_runs(dag_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dag_runs']


def fetch_task_instances(dag_id, dag_run_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances", auth=airflow_auth)
    response.raise_for_status()
    #res = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/tasks", auth=airflow_auth)
    return response.json()['task_instances']


def calculate_duration(start_time, end_time):
    # Calculate duration if both times are available
    if start_time and end_time:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = (end - start).total_seconds() #/ 60  # Duration in seconds
        return duration
        #return round(duration, 2)
    return None


def inspect_dag_runs():
    dags = fetch_dags()

    for dag in dags:
        dag_id = dag['dag_id']
        dag_runs = fetch_dag_runs(dag_id)

        print(f"\nDAG ID: {dag_id}")
        for dag_run in dag_runs:
            dag_run_id = dag_run['dag_run_id']
            print("DAG Run Details:")
            for key, value in dag_run.items():
                print(f"  {key}: {value}")

            # Fetch and print all task instance details for each DAG run
            task_instances = fetch_task_instances(dag_id, dag_run_id)
            print("  Task Instances:")
            for task in task_instances:
                print(f"    Task ID: {task['task_id']}")

                queued_dttm = task.get('queued_when')
                start_date = task.get('start_date')
                queued_duration = calculate_duration(queued_dttm, start_date)

                print(f"      Queued Duration (seconds): {queued_duration}")
                start_date_str = task.get('start_date')
                end_date_str = task.get('end_date')

                # Ensure both dates are strings and not None
                if isinstance(start_date_str, str) and isinstance(end_date_str, str):
                    # Convert strings to datetime objects
                    start_date = datetime.fromisoformat(start_date_str)
                    end_date = datetime.fromisoformat(end_date_str)

                    # Calculate run duration
                    run_duration_seconds = (end_date - start_date).total_seconds()
                    run_duration_minutes = run_duration_seconds / 60
                    print(f"Run Duration: {run_duration_minutes:.2f} minutes")
                else:
                    print("Start or end date is missing or not a valid string.")
                for key, value in task.items():
                    print(f"      {key}: {value}")
                print()  # Print a newline for better readability


def main():
    inspect_dag_runs()


if __name__ == "__main__":
    main()