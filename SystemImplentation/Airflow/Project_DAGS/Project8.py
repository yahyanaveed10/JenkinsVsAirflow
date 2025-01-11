import os

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime, timedelta

from Python_Libs.env_vars import create_env_vars

default_args = {
        'owner': 'airflow_admin',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'start_date': datetime(2024, 10, 28),
        'retries': 30,   # Number of times to retry if a task fails
        'retry_delay': timedelta(minutes=10),  # Delay between retries
}

with DAG(
        dag_id='Project8',
        default_args=default_args,
        tags=['Projects'],
        #schedule_interval='0 1 * * *',  # 1 AM and 1 PM
        #catchup=True
    ) as dag:
    kube_pod_operator_task_0 = KubernetesPodOperator(
        task_id='kube_pod_operator_task_0',
        kubernetes_conn_id="<connection_id>",
        service_account_name='default',
        name='<Pod_name>',
        namespace='<namespace>',
        image='<image_name>',
        env_vars=create_env_vars( os.getenv('env_vars')),
        in_cluster=False,
        image_pull_policy='Always',
        get_logs=True,
        image_pull_secrets=[{"name": "<secret>"}],
        container_resources={
            'requests': {'memory': "200Mi", 'cpu': "100m"},
            'limits': {'memory': "5Gi", 'cpu': "1"}
        },
        is_delete_operator_pod=False,
        execution_timeout=timedelta(hours=20)
    )

    