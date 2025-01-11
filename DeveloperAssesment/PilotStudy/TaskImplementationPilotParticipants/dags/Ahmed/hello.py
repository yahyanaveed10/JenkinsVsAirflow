from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

# Define default arguments that will be passed to all tasks in the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['your-email@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Create the DAG object
dag = DAG(
    'simple_data_pipeline',
    default_args=default_args,
    description='A simple Airflow pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Define a Python function that will be executed by our task
def process_data(**context):
    """
    A simple function that processes some data.
    In this example, we're just printing a message.
    """
    print("Processing data...")
    # You could add your data processing logic here
    data_value = 42
    # Push a value to XCom for the next task to use
    context['task_instance'].xcom_push(key='processed_value', value=data_value)
    print("Data processing completed!")

def analyze_results(**context):
    """
    Function to analyze the results from the previous task.
    """
    # Pull the value from the previous task using XCom
    processed_value = context['task_instance'].xcom_pull(
        key='processed_value',
        task_ids='process_data_task'
    )
    print(f"Analyzing results... Processed value was: {processed_value}")
    # Add your analysis logic here

# Create tasks
start_pipeline = BashOperator(
    task_id='start_pipeline',
    bash_command='echo "Pipeline starting..."',
    dag=dag
)

process_data_task = PythonOperator(
    task_id='process_data_task',
    python_callable=process_data,
    provide_context=True,
    dag=dag
)

analyze_results_task = PythonOperator(
    task_id='analyze_results_task',
    python_callable=analyze_results,
    provide_context=True,
    dag=dag
)

end_pipeline = BashOperator(
    task_id='end_pipeline',
    bash_command='echo "Pipeline completed!"',
    dag=dag
)

# Set task dependencies
start_pipeline >> process_data_task >> analyze_results_task >> end_pipeline