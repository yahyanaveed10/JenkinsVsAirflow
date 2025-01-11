import time

import requests
from requests.auth import HTTPBasicAuth
import psycopg2
from datetime import datetime, timezone

# Airflow API URL and authentication
AIRFLOW_API_URL = "https://<airflow>/api/v1"
AIRFLOW_USER = "<airflow_user>"
AIRFLOW_PASS = "<airflow_pass>"
JENKINS_API_URL = "https://<jenkins>/api/json"
JENKINS_USER = "<jenkins_user>"
JENKINS_PASS = "<jenkins_pass>"
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "metrics_db"
PG_USER = "your_user"
PG_PASS = "your_password"
airflow_auth = HTTPBasicAuth(AIRFLOW_USER, AIRFLOW_PASS)

THRESHOLD_DATE = datetime.fromisoformat("2024-11-12T00:00:00+00:00")


def is_date_greater_than_threshold(date_string):
    """
    Compare if a date string is greater than the threshold date
    Args:
        date_string: ISO format date string
    Returns:
        bool: True if date is greater than threshold, False otherwise
    """
    if not date_string:
        return False
    try:
        # Convert the input string to datetime object
        date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        #print(THRESHOLD_DATE)
        return date >= THRESHOLD_DATE
    except (ValueError, TypeError):
        return False


def parse_date(date_string):
    """Parse date string to datetime object"""
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except ValueError:
        return None


def calculate_duration(start_time, end_time):
    """Calculate duration between two timestamps"""
    if not (start_time and end_time):
        return None

    start = parse_date(start_time)
    end = parse_date(end_time)

    if start and end:
        return (end - start).total_seconds()
    return None


def fetch_dags():
    response = requests.get(f"{AIRFLOW_API_URL}/dags", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dags']


def fetch_dag_runs(dag_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dag_runs']


def fetch_task_instances(dag_id, dag_run_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['task_instances']


def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS airflow_dag_runs (
                dag_id VARCHAR(255),
                dag_run_id VARCHAR(255) PRIMARY KEY,
                execution_date TIMESTAMP WITH TIME ZONE,
                start_date TIMESTAMP WITH TIME ZONE,
                end_date TIMESTAMP WITH TIME ZONE,
                state VARCHAR(50),
                run_type VARCHAR(50),
                run_duration FLOAT,
                queued_duration FLOAT
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS airflow_task_instances_v2 (
                dag_id VARCHAR(255),
                dag_run_id VARCHAR(255),
                task_id VARCHAR(255),
                start_date TIMESTAMP WITH TIME ZONE,
                end_date TIMESTAMP WITH TIME ZONE,
                state VARCHAR(50),
                run_duration FLOAT,
                queued_duration FLOAT,
                max_tries INTEGER,
                execution_date TIMESTAMP WITH TIME ZONE,
                queued_when TIMESTAMP WITH TIME ZONE,
                duration FLOAT,
                PRIMARY KEY (dag_run_id, task_id),
                FOREIGN KEY (dag_run_id) REFERENCES airflow_dag_runs(dag_run_id)
            );
        """)
        conn.commit()


def store_dag_run(conn, dag_run, dag_id):
    with conn.cursor() as cur:
        run_duration = calculate_duration(dag_run.get('start_date'), dag_run.get('end_date'))
        queued_duration = calculate_duration(dag_run.get('queued_when'), dag_run.get('start_date'))

        cur.execute("""
            INSERT INTO airflow_dag_runs (
                dag_id, dag_run_id, execution_date, start_date, end_date, 
                state, run_type, run_duration, queued_duration
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dag_run_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                state = EXCLUDED.state,
                run_duration = EXCLUDED.run_duration,
                queued_duration = EXCLUDED.queued_duration;
        """, (
            dag_id,
            dag_run['dag_run_id'],
            parse_date(dag_run['execution_date']),
            parse_date(dag_run.get('start_date')),
            parse_date(dag_run.get('end_date')),
            dag_run['state'],
            dag_run['run_type'],
            run_duration,
            queued_duration
        ))
        conn.commit()


def store_task_instance_v2(conn, dag_run_id, task, dag_id):
    with conn.cursor() as cur:
        run_duration = calculate_duration(task.get('start_date'), task.get('end_date'))
        queued_duration = calculate_duration(task.get('queued_when'), task.get('start_date'))

        cur.execute("""
            INSERT INTO airflow_task_instances_v2 (
                dag_id, dag_run_id, task_id, start_date, end_date, state,
                run_duration, queued_duration, max_tries, execution_date,
                queued_when, duration
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dag_run_id, task_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                state = EXCLUDED.state,
                run_duration = EXCLUDED.run_duration,
                queued_duration = EXCLUDED.queued_duration,
                max_tries = EXCLUDED.max_tries,
                execution_date = EXCLUDED.execution_date,
                queued_when = EXCLUDED.queued_when,
                duration = EXCLUDED.duration;
        """, (
            dag_id,
            dag_run_id,
            task['task_id'],
            parse_date(task.get('start_date')),
            parse_date(task.get('end_date')),
            task['state'],
            run_duration,
            queued_duration,
            task.get('max_tries'),
            parse_date(task.get('execution_date')),
            parse_date(task.get('queued_when')),
            task.get('duration')
        ))
        conn.commit()


def main():
    conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        host=PG_HOST,
        port=PG_PORT
    )

    try:
        create_tables(conn)
        dags = fetch_dags()
        for dag in dags:
            dag_id = dag['dag_id']
            dag_runs = fetch_dag_runs(dag_id)

            for dag_run in dag_runs:
                if is_date_greater_than_threshold(dag_run.get('start_date')):
                    store_dag_run(conn, dag_run, dag_id)
                    task_instances = fetch_task_instances(dag_id, dag_run['dag_run_id'])
                    for task in task_instances:
                        if is_date_greater_than_threshold(task.get('start_date')):
                            store_task_instance_v2(conn, dag_run['dag_run_id'], task, dag_id)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
  #while True:
    main()
    print("Imported!")
    #time.sleep(60)
