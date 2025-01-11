from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
# Define the function to be executed
def hello_world():
    print("Hello, World!")
#Create the DAG
default_args = { 'owner': 'rayed',
                 'retries': 1,
                 'retry_delay': timedelta(minutes=5),
            }
with DAG( dag_id='hello_world_dag', default_args=default_args, description='A simple Hello World DAG', start_date=datetime(2024, 12, 1),
# Ensure this is in the past
schedule_interval=None,
# Set to None to run manually
catchup=False, ) as dag:
# Define the Python task
    hello_world_task = PythonOperator( task_id='print_hello_world', python_callable=hello_world, )

hello_world_task