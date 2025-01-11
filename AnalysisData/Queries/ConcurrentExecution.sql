WITH dag_times AS (
    SELECT
        COUNT(DISTINCT CASE WHEN state = 'success' THEN dag_id END) as successful_dags,
        COUNT(DISTINCT CASE WHEN state = 'failed' THEN dag_id END) as failed_dags,
        MIN(execution_date) AS min_execution_date,
        MAX(execution_date + INTERVAL '1 second' * run_duration) AS max_end_time
    FROM thesis_airflow_dag_runs
    WHERE execution_date BETWEEN $__timeFrom() AND $__timeTo()
    AND state IN ('success', 'failed')
),
jenkins_times AS (
    SELECT
        COUNT(DISTINCT CASE WHEN build_status IN ('SUCCESS', 'UNSTABLE') THEN job_name END) as successful_jobs,
        COUNT(DISTINCT CASE WHEN build_status = 'FAILURE' THEN job_name END) as failed_jobs,
        MIN(start_time) AS min_start_time,
        MAX(start_time + INTERVAL '1 second' * total_duration_seconds) AS max_end_time
    FROM thesis_jenkins_builds
    WHERE start_time BETWEEN $__timeFrom() AND $__timeTo()
    AND build_status IN ('SUCCESS', 'UNSTABLE', 'FAILURE')
)
SELECT
    'Airflow' as platform,
    successful_dags as successful_pipelines,
    failed_dags as failed_pipelines,
    DATE_TRUNC('minute', min_execution_date) AS start_time,
    DATE_TRUNC('minute', max_end_time) AS end_time,
    EXTRACT(EPOCH FROM max_end_time - min_execution_date)/3600 AS duration_hours
FROM dag_times
UNION ALL
SELECT
    'Jenkins' as platform,
    successful_jobs as successful_pipelines,
    failed_jobs as failed_pipelines,
    DATE_TRUNC('minute', min_start_time) AS start_time,
    DATE_TRUNC('minute', max_end_time) AS end_time,
    EXTRACT(EPOCH FROM max_end_time - min_start_time)/3600 AS duration_hours
FROM jenkins_times
ORDER BY platform;