import requests
from requests.auth import HTTPBasicAuth
import psycopg2
from datetime import datetime

# Airflow API URL and authentication
AIRFLOW_API_URL = "https://airflow-vm-tamer-instance-ci-airflow-poc.apps.de3pro.osh.ipz001.internal.bosch.cloud/api/v1"
AIRFLOW_USER = "airflow-vm-tamer-instance-restapi"
AIRFLOW_PASS = "6iuQseSesDFT"
JENKINS_API_URL = "https://rb-jmaas.de.bosch.com/CC-AS_TAMER_Export/api/json"
JENKINS_USER = "say3abt"
JENKINS_PASS = "118a30649b68cd182ae2534f5eb13345cb"
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "metrics_db"
PG_USER = "your_user"
PG_PASS = "your_password"
airflow_auth = HTTPBasicAuth(AIRFLOW_USER, AIRFLOW_PASS)



def fetch_dags():
    response = requests.get(f"{AIRFLOW_API_URL}/dags", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dags']

# Fetch DAG runs for a specific DAG
def fetch_dag_runs(dag_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dag_runs']

# Fetch task instances for a specific DAG run
def fetch_task_instances(dag_id, dag_run_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['task_instances']

# Create the required tables
def create_tables(conn):
    with conn.cursor() as cur:
        # DAG runs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS airflow_dag_runs (
                dag_id VARCHAR(255),
                dag_run_id VARCHAR(255) PRIMARY KEY,
                execution_date TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                state VARCHAR(50),
                run_type VARCHAR(50),
                run_duration FLOAT,
                queued_duration FLOAT
            );
        """)
        # Task instances table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS airflow_task_instances (
                dag_id VARCHAR(255),
                dag_run_id VARCHAR(255),
                task_id VARCHAR(255),
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                state VARCHAR(50),
                run_duration FLOAT,
                queued_duration FLOAT,
                PRIMARY KEY (dag_run_id, task_id),
                FOREIGN KEY (dag_run_id) REFERENCES airflow_dag_runs(dag_run_id)
            );
        """)
        conn.commit()

# Calculate the duration between two timestamps
def calculate_duration(start_time, end_time):
    if start_time and end_time:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        return (end - start).total_seconds()
    return None

# Insert or update DAG run details
def store_dag_run(conn, dag_run, dag_id):
    with conn.cursor() as cur:
        run_duration = calculate_duration(dag_run.get('start_date'), dag_run.get('end_date'))
        queued_duration = calculate_duration(dag_run.get('queued_when'), dag_run.get('start_date'))

        cur.execute("""
            INSERT INTO airflow_dag_runs (dag_id, dag_run_id, execution_date, start_date, end_date, state, run_type, run_duration, queued_duration)
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
            dag_run['execution_date'],
            dag_run.get('start_date'),
            dag_run.get('end_date'),
            dag_run['state'],
            dag_run['run_type'],
            run_duration,
            queued_duration
        ))
        conn.commit()

# Insert or update task instance details
def store_task_instance(conn, dag_run_id, task, dag_id):
    with conn.cursor() as cur:
        run_duration = calculate_duration(task.get('start_date'), task.get('end_date'))
        queued_duration = calculate_duration(task.get('queued_when'), task.get('start_date'))

        cur.execute("""
            INSERT INTO airflow_task_instances (dag_id, dag_run_id, task_id, start_date, end_date, state, run_duration, queued_duration)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dag_run_id, task_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                state = EXCLUDED.state,
                run_duration = EXCLUDED.run_duration,
                queued_duration = EXCLUDED.queued_duration;
        """, (
            dag_id,
            dag_run_id,
            task['task_id'],
            task.get('start_date'),
            task.get('end_date'),
            task['state'],
            run_duration,
            queued_duration
        ))
        conn.commit()

# Main function to fetch and store DAG and task data
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
                store_dag_run(conn, dag_run, dag_id)
                task_instances = fetch_task_instances(dag_id, dag_run['dag_run_id'])
                for task in task_instances:
                    store_task_instance(conn, dag_run['dag_run_id'], task, dag_id)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()