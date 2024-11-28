# dags/github_dag.py
from airflow import DAG
from airflow.providers.github.operators.github import GithubOperator
from datetime import datetime

default_args = {
   'owner': 'airflow',
   'start_date': datetime(2024, 1, 1)
}

dag = DAG('github_repo_check',
         default_args=default_args,
         schedule_interval='@daily')

check_repo = GithubOperator(
   task_id='check_repo',
   github_conn_id='github_default',
   github_method='get_repo',
   github_method_args={'yahadpas@gmail.com': 'yahyanaveed10/JenkinsVsAirflow'},
   dag=dag
)