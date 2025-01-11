import time

import psycopg2
import time
import logging
from typing import Optional
from contextlib import contextmanager
import sys

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

JENKINS_URL = "<jenkins>"
USERNAME = '<user>'
API_TOKEN = '<pass>'


DB_CONFIG = {
    'dbname': 'metrics_db',
    'user': 'your_user',
    'password': 'your_password',
    'host': 'localhost'
}


# Connect to the database
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Create tables if they don't exist
def setup_database():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jenkins_nodes (
                node_id SERIAL PRIMARY KEY,
                display_name VARCHAR(255),
                num_executors INTEGER,
                idle BOOLEAN,
                available_physical_memory BIGINT,
                total_physical_memory BIGINT,
                available_disk_space BIGINT,
                total_disk_space BIGINT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jenkins_jobs (
                job_id SERIAL PRIMARY KEY,
                node_id INTEGER REFERENCES jenkins_nodes(node_id),
                job_name VARCHAR(255),
                build_url VARCHAR(255),
                duration BIGINT,
                result VARCHAR(50),
                executor VARCHAR(255),
                start_time TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    conn.close()

# Insert or update node information in the database
def save_node_info(db_conn, node_info):
    with db_conn.cursor() as cursor:
        for info in node_info:
            # Convert "N/A" to None for numerical fields
            available_physical_memory = info['availablePhysicalMemory'] if info['availablePhysicalMemory'] != 'N/A' else None
            total_physical_memory = info['totalPhysicalMemory'] if info['totalPhysicalMemory'] != 'N/A' else None
            available_disk_space = info['availableDiskSpace'] if info['availableDiskSpace'] != 'N/A' else None
            total_disk_space = info['totalDiskSpace'] if info['totalDiskSpace'] != 'N/A' else None

            cursor.execute("""
                INSERT INTO jenkins_nodes (display_name, num_executors, idle, available_physical_memory, 
                                           total_physical_memory, available_disk_space, total_disk_space, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING node_id
            """, (
                info['displayName'], info['numExecutors'], info['idle'], available_physical_memory,
                total_physical_memory, available_disk_space, total_disk_space, datetime.now()
            ))
            node_id = cursor.fetchone()[0]

            # Insert job information associated with this node
            for job in info['jobs']:
                cursor.execute("""
                    INSERT INTO jenkins_jobs (node_id, job_name, build_url, duration, result, executor, start_time, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    node_id, job['job_name'], job['build_url'],
                    job['build_info']['duration'] if job['build_info']['duration'] != 'N/A' else None,
                    job['build_info']['result'], job['build_info']['executor'],
                    datetime.fromtimestamp(job['build_info']['start_time'] / 1000) if job['build_info']['start_time'] != 'N/A' else None,
                    datetime.now()
                ))
    db_conn.commit()

# Fetch build information for a specific job
def get_build_info(build_url):
    response = requests.get(f"{build_url}api/json", auth=HTTPBasicAuth(USERNAME, API_TOKEN))
    if response.status_code == 200:
        build_data = response.json()
        return {
            'duration': build_data.get('duration', 'N/A'),
            'result': build_data.get('result', 'N/A'),
            'executor': build_data.get('executor', 'N/A'),
            'start_time': build_data.get('timestamp', 'N/A')
        }
    else:
        print(f"Error fetching build data: {response.status_code} - {response.reason}")
        return None

# Fetch Jenkins node and job information
def get_jenkins_node_info():
    response = requests.get(f"{JENKINS_URL}/computer/api/json", auth=HTTPBasicAuth(USERNAME, API_TOKEN))
    if response.status_code == 200:
        data = response.json()
        node_info = []

        for computer in data.get('computer', []):
            info = {
                'displayName': computer.get('displayName', 'N/A'),
                'numExecutors': computer.get('numExecutors', 'N/A'),
                'idle': computer.get('idle', 'N/A'),
                'monitorData': computer.get('monitorData', {}),
                'jobs': []
            }

            swap_monitor = info['monitorData'].get('hudson.node_monitors.SwapSpaceMonitor')
            if swap_monitor:
                info['availablePhysicalMemory'] = swap_monitor.get('availablePhysicalMemory', 'N/A')
                info['totalPhysicalMemory'] = swap_monitor.get('totalPhysicalMemory', 'N/A')
            else:
                info['availablePhysicalMemory'] = 'N/A'
                info['totalPhysicalMemory'] = 'N/A'

            disk_monitor = info['monitorData'].get('hudson.node_monitors.DiskSpaceMonitor')
            if disk_monitor:
                info['availableDiskSpace'] = disk_monitor.get('size', 'N/A')
                info['totalDiskSpace'] = disk_monitor.get('totalSize', 'N/A')
            else:
                info['availableDiskSpace'] = 'N/A'
                info['totalDiskSpace'] = 'N/A'

            executors = computer.get('executors', [])
            for executor in executors:
                current_executable = executor.get('currentExecutable')
                if current_executable:
                    job_name = current_executable.get('fullDisplayName', 'N/A')
                    build_url = current_executable.get('url', 'N/A')
                    build_info = get_build_info(build_url)

                    info['jobs'].append({
                        'job_name': job_name,
                        'build_url': build_url,
                        'build_info': build_info
                    })

            node_info.append(info)
        return node_info
    else:
        print(f"Error fetching node data: {response.status_code} - {response.reason}")
        return None


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('jenkins_monitor.log')
    ]
)
logger = logging.getLogger(__name__)


@contextmanager
def database_connection():
    """Context manager for database connections with automatic reconnection"""
    connection = None
    try:
        connection = get_db_connection()
        yield connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.close()
        raise
    finally:
        if connection:
            connection.close()


def retry_on_error(max_retries: int = 3, delay: int = 5):
    """Decorator for retrying functions on failure"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached. Last error: {e}")
                        raise
                    logger.warning(f"Attempt {retries}/{max_retries} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


@retry_on_error(max_retries=3, delay=5)
def get_jenkins_node_info_with_retry() -> Optional[dict]:
    """Wrapper for get_jenkins_node_info with retry logic"""
    return get_jenkins_node_info()


@retry_on_error(max_retries=3, delay=5)
def save_node_info_with_retry(conn, nodes):
    """Wrapper for save_node_info with retry logic"""
    save_node_info(conn, nodes)


def main_loop():
    """Main execution loop with error handling"""
    while True:
        try:
            # Setup database if needed
            setup_database()

            # Get and save node information
            with database_connection() as db_conn:
                nodes = get_jenkins_node_info_with_retry()
                if nodes is not None:
                    save_node_info_with_retry(db_conn, nodes)
                    logger.info("Data saved to the database successfully.")
                else:
                    logger.warning("No node information retrieved.")

                # Wait before next iteration
                time.sleep(3)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.info("Restarting main loop in 10 seconds...")
            time.sleep(10)


if __name__ == '__main__':
    logger.info("Starting Jenkins node monitoring service")
    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Critical error in service: {e}")
            logger.info("Restarting service in 30 seconds...")
            time.sleep(30)

