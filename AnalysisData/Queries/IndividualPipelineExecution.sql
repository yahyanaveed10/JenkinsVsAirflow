WITH TaskTimings AS (
    SELECT
        dag_id,
        dag_run_id,
        execution_date,
        start_date,
        end_date,
        state,
        ROW_NUMBER() OVER (PARTITION BY dag_id ORDER BY execution_date) as execution_number
    FROM thesis_airflow_task_instances_v2
    WHERE state = 'success'
    AND DATE(execution_date) IN ('2024-11-06', '2024-11-08', '2024-11-12', '2024-11-13', '2024-11-14')
),
DAGRunTimes AS (
    SELECT
        dag_id,
        dag_run_id,
        execution_number,
        EXTRACT(EPOCH FROM (MAX(end_date) - MIN(start_date))) as duration,
        MIN(start_date) as start_time
    FROM TaskTimings
    GROUP BY dag_id, dag_run_id, execution_number
),
JenkinsRuns AS (
    SELECT
        job_name,
        run_duration_without_queue as duration,
        build_status,
        start_time,
        ROW_NUMBER() OVER (PARTITION BY job_name ORDER BY start_time) as execution_number
    FROM thesis_jenkins_builds
    WHERE (build_status = 'UNSTABLE' OR build_status = 'SUCCESS' OR build_status = 'FAILURE')
    AND DATE(start_time) IN ('2024-11-06', '2024-11-08', '2024-11-12', '2024-11-13', '2024-11-14')
),
MinExecutions AS (
    SELECT job_name, MIN(exec_count) as min_executions
    FROM (
        SELECT dag_id as job_name, COUNT(*) as exec_count
        FROM DAGRunTimes
        GROUP BY dag_id
        UNION ALL
        SELECT job_name, COUNT(*) as exec_count
        FROM JenkinsRuns
        GROUP BY job_name
    ) counts
    GROUP BY job_name
),
BasicStats AS (
    SELECT
        'Airflow' as platform,
        d.dag_id as pipeline_name,
        COUNT(*) as num_executions,
        ROUND(AVG(d.duration)::numeric, 2) as avg_execution_time_seconds,
        ROUND(STDDEV(d.duration)::numeric, 2) as std_dev_seconds,
        ROUND(MIN(d.duration)::numeric, 2) as min_duration,
        ROUND(MAX(d.duration)::numeric, 2) as max_duration,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY d.duration)::numeric, 2) as median_duration,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY d.duration)::numeric, 2) as p95_duration,
        COUNT(CASE WHEN d.duration > 3600 THEN 1 END) as long_running_count
    FROM DAGRunTimes d
    JOIN MinExecutions m ON d.dag_id = m.job_name
    WHERE d.execution_number <= m.min_executions
    GROUP BY d.dag_id
    UNION ALL
    SELECT
        'Jenkins' as platform,
        j.job_name as pipeline_name,
        COUNT(*) as num_executions,
        ROUND(AVG(j.duration)::numeric, 2) as avg_execution_time_seconds,
        ROUND(STDDEV(j.duration)::numeric, 2) as std_dev_seconds,
        ROUND(MIN(j.duration)::numeric, 2) as min_duration,
        ROUND(MAX(j.duration)::numeric, 2) as max_duration,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY j.duration)::numeric, 2) as median_duration,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY j.duration)::numeric, 2) as p95_duration,
        COUNT(CASE WHEN j.duration > 3600 THEN 1 END) as long_running_count
    FROM JenkinsRuns j
    JOIN MinExecutions m ON j.job_name = m.job_name
    WHERE j.execution_number <= m.min_executions
    GROUP BY j.job_name
),
Improvements AS (
    SELECT
        a.pipeline_name,
        ROUND(((j.avg_execution_time_seconds - a.avg_execution_time_seconds) / NULLIF(j.avg_execution_time_seconds, 0) * 100)::numeric, 2) as performance_improvement_pct,
        ROUND(((j.std_dev_seconds - a.std_dev_seconds) / NULLIF(a.std_dev_seconds, 0) * 100)::numeric, 2) as stability_improvement_pct,
        ROUND(((j.p95_duration - a.p95_duration) / NULLIF(a.p95_duration, 0) * 100)::numeric, 2) as p95_improvement_pct
    FROM BasicStats a
    JOIN BasicStats j ON a.pipeline_name = j.pipeline_name
    WHERE a.platform = 'Airflow' AND j.platform = 'Jenkins'
)
SELECT
    b.*,
    i.performance_improvement_pct,
    i.stability_improvement_pct,
    i.p95_improvement_pct,
    CASE
        WHEN b.avg_execution_time_seconds < 1800 THEN 'Short'
        WHEN b.avg_execution_time_seconds < 3600 THEN 'Medium'
        ELSE 'Long'
    END as execution_category
FROM BasicStats b
LEFT JOIN Improvements i ON b.pipeline_name = i.pipeline_name
ORDER BY b.platform, b.avg_execution_time_seconds DESC;
