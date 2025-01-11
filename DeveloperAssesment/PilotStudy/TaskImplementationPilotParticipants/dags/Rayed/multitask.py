from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import random

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['your_email@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'weather_information_dag',
    default_args=default_args,
    description='A DAG to fetch weather information using parallel tasks and XCom',
    schedule_interval=timedelta(days=1),
    catchup=False
)


def get_temperature(**context):
    """
    First operator: Get temperature and push to XCom
    Simulating an API call to get temperature
    """
    # Simulate getting temperature from a weather API
    temperature = random.uniform(15.0, 30.0)
    # Push the temperature to XCom
    context['task_instance'].xcom_push(key='temperature', value=temperature)
    return f"Temperature recorded: {temperature}°C"


def get_weather_condition(**context):
    """
    Second operator: Get weather condition and push to XCom
    Simulating an API call to get weather condition
    """
    # Simulate getting weather condition from a weather API
    conditions = ['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy']
    condition = random.choice(conditions)
    # Push the condition to XCom
    context['task_instance'].xcom_push(key='condition', value=condition)
    return f"Weather condition recorded: {condition}"


def print_weather_info(**context):
    """
    Third operator: Pull data from XCom and combine information
    """
    # Pull temperature and condition from XCom
    task_instance = context['task_instance']
    temperature = task_instance.xcom_pull(key='temperature', task_ids='get_temperature_task')
    condition = task_instance.xcom_pull(key='condition', task_ids='get_weather_condition_task')

    # Combine and print the information
    weather_report = f"Current Weather Report:\nTemperature: {temperature:.1f}°C\nCondition: {condition}"
    print(weather_report)
    return weather_report


# Create the operators
get_temperature_task = PythonOperator(
    task_id='get_temperature_task',
    python_callable=get_temperature,
    provide_context=True,
    dag=dag,
)

get_weather_condition_task = PythonOperator(
    task_id='get_weather_condition_task',
    python_callable=get_weather_condition,
    provide_context=True,
    dag=dag,
)

print_weather_info_task = PythonOperator(
    task_id='print_weather_info_task',
    python_callable=print_weather_info,
    provide_context=True,
    dag=dag,
)

# Set up task dependencies
[get_temperature_task, get_weather_condition_task] >> print_weather_info_task