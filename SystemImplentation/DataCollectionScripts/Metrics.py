from datetime import datetime

import requests
import psycopg2
import json
from requests.auth import HTTPBasicAuth
import os
import psutil

# Configuration
AIRFLOW_API_URL = "<airflowurl>"
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

# Auth setup for Airflow and Jenkins
airflow_auth = HTTPBasicAuth(AIRFLOW_USER, AIRFLOW_PASS)
jenkins_auth = HTTPBasicAuth(JENKINS_USER, JENKINS_PASS)

def fetch_dags():
    response = requests.get(f"{AIRFLOW_API_URL}/dags", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dags']

def fetch_dag_runs(dag_id):
    response = requests.get(f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns", auth=airflow_auth)
    response.raise_for_status()
    return response.json()['dag_runs']

def fetch_jenkins_jobs():
    response = requests.get(f"{JENKINS_API_URL}/jobs", auth=jenkins_auth)
    response.raise_for_status()
    return response.json()['jobs']

def fetch_jenkins_builds(job_name):
    response = requests.get(f"{JENKINS_API_URL}/job/{job_name}/api/json?tree=lastBuild[url]", auth=jenkins_auth)
    response.raise_for_status()
    return response.json()['builds']

def create_table_if_not_exists(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                dag_id VARCHAR(255),
                dag_run_id VARCHAR(255),
                execution_date TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                state VARCHAR(50),
                run_type VARCHAR(50),
                PRIMARY KEY (dag_id, dag_run_id)
            );
        """)
        conn.commit()

def store_metrics(data, conn, table_name):
    with conn.cursor() as cur:
        for record in data:
            cur.execute(f"""
                INSERT INTO {table_name} (dag_id, dag_run_id, execution_date, start_date, end_date, state, run_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dag_id, dag_run_id) DO UPDATE
                SET start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    state = EXCLUDED.state;
            """, (
                record['dag_id'],
                record['dag_run_id'],
                record['execution_date'],
                record.get('start_date'),
                record.get('end_date'),
                record['state'],
                record['run_type']
            ))
        conn.commit()

def parse_datetime(datetime_str):
    """Parse the datetime string from Airflow into a datetime object."""
    if datetime_str:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    return None


def get_system_memory_usage():
    """Returns the current system memory usage as a percentage."""
    return psutil.virtual_memory().percent

def parse_datetime(datetime_str):
    """Parse the datetime string from Airflow into a datetime object."""
    if datetime_str:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    return None

def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        host=PG_HOST,
        port=PG_PORT
    )

    try:
        # Fetch and store Airflow DAG runs
        create_table_if_not_exists(conn, 'airflow_metrics')
        dags = fetch_dags()
        for dag in dags:
            dag_id = dag['dag_id']
            dag_runs = fetch_dag_runs(dag_id)

            processed_runs = [
                {
                    "dag_id": dag_run['dag_id'],
                    "dag_run_id": dag_run['dag_run_id'],
                    "execution_date": dag_run['execution_date'],
                    "start_date": dag_run.get('start_date'),
                    "end_date": dag_run.get('end_date'),
                    "state": dag_run['state'],
                    "run_type": dag_run['run_type']
                }
                for dag_run in dag_runs
            ]
            store_metrics(processed_runs, conn, 'airflow_metrics')
        # Fetch and store Jenkins job builds
        # jobs = fetch_jenkins_jobs()
        # for job in jobs:
        #     job_name = job['name']
        #     builds = fetch_jenkins_builds(job_name)
        #     processed_builds = [
        #         {
        #             "pipeline": job_name,
        #             "execution_date": datetime.utcfromtimestamp(build['timestamp'] / 1000).isoformat(),
        #             "start_date": None,
        #             "end_date": None,
        #             "state": 'SUCCESS' if build['duration'] > 0 else 'FAILED',  # Simplified for example
        #             "execution_time": build['duration'] / 1000,  # Jenkins API returns milliseconds
        #             "memory_usage": get_system_memory_usage()
        #         }
        #         for build in builds
        #     ]
        #     store_metrics(processed_builds, conn, 'jenkins_metrics')

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()