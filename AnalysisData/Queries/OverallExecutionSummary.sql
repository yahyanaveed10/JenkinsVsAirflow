WITH latest_airflow_runs AS (
    -- Get Airflow runs for the specified dates
    SELECT
        'Airflow' as system,
        start_date as start_time,
        end_date as end_time,
        state as status,
        dag_run_id::text as run_id
    FROM thesis_airflow_dag_runs
    WHERE state != 'skipped'
    AND start_date IS NOT NULL
    AND end_date IS NOT NULL
    AND dag_run_id IS NOT NULL
    AND DATE(start_date) IN ('2024-11-06', '2024-11-08', '2024-11-12', '2024-11-13', '2024-11-14')
    ORDER BY start_date DESC
    Limit 439
),
latest_jenkins_runs AS (
    -- Get Jenkins runs for the specified dates
    SELECT
        'Jenkins' as system,
        start_time,
        end_time,
        build_status as status,
        build_number::text as run_id
    FROM thesis_jenkins_builds
    WHERE build_status != 'ABORTED'
    AND total_duration_seconds > 0
    AND start_time IS NOT NULL
    AND end_time IS NOT NULL
    AND build_number > 0
    AND build_number IS NOT NULL
    AND DATE(start_time) IN ('2024-11-06', '2024-11-08', '2024-11-12', '2024-11-13', '2024-11-14')
    ORDER BY start_time DESC
    Limit 439
),
latest_runs AS (
    -- Combine both Airflow and Jenkins runs
    SELECT * FROM latest_airflow_runs
    UNION ALL
    SELECT * FROM latest_jenkins_runs
),
base_metrics AS (
    -- Aggregates for both Airflow and Jenkins
    SELECT
        system,
        COUNT(*) as total_runs,
        COUNT(CASE
            WHEN system = 'Airflow' AND status = 'success' THEN 1
            WHEN system = 'Jenkins' AND (status = 'SUCCESS' OR status = 'UNSTABLE') THEN 1
            ELSE NULL
        END) as successful_runs,
        COUNT(CASE
            WHEN system = 'Airflow' AND status != 'success' THEN 1
            WHEN system = 'Jenkins' AND status = 'FAILURE' THEN 1
            ELSE NULL
        END) as failed_runs,
        ROUND(CAST((COUNT(CASE
            WHEN system = 'Airflow' AND status = 'success' THEN 1
            WHEN system = 'Jenkins' AND (status = 'SUCCESS' OR status = 'UNSTABLE') THEN 1
            ELSE NULL
        END)::decimal /
            NULLIF(COUNT(*), 0) * 100) as numeric), 2) as success_rate,
        ROUND(CAST((COUNT(CASE
            WHEN system = 'Airflow' AND status != 'success' THEN 1
            WHEN system = 'Jenkins' AND status = 'FAILURE' THEN 1
            ELSE NULL
        END)::decimal /
            NULLIF(COUNT(*), 0) * 100) as numeric), 2) as failure_rate,
        MIN(EXTRACT(EPOCH FROM (end_time - start_time))) as min_duration_seconds,
        MAX(EXTRACT(EPOCH FROM (end_time - start_time))) as max_duration_seconds,
        AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (end_time - start_time))) as median_duration_seconds,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (end_time - start_time))) as p95_duration_seconds,
        MIN(start_time) as period_start,
        MAX(start_time) as period_end
    FROM latest_runs
    GROUP BY system
)
SELECT
    system,
    period_start,
    period_end,
    total_runs,
    successful_runs,
    failed_runs,
    success_rate,
    failure_rate,
    CAST(min_duration_seconds/60 as numeric) as min_duration_minutes,
    CAST(max_duration_seconds/60 as numeric) as max_duration_minutes,
    CAST(avg_duration_seconds/60 as numeric) as avg_duration_minutes,
    CAST(median_duration_seconds/60 as numeric) as median_duration_minutes,
    CAST(p95_duration_seconds/60 as numeric) as p95_duration_minutes,
    -- Based on Travis CI study (Hilton et al., 2016)
    CASE
        WHEN success_rate >= 90 THEN 'High Reliability'
        WHEN success_rate >= 75 THEN 'Medium Reliability'
        ELSE 'Low Reliability'
    END as travis_reliability_rating,
    -- Based on GitLab CI Metrics
    CASE
        WHEN success_rate >= 95 THEN 'Excellent'
        WHEN success_rate >= 85 THEN 'Good'
        ELSE 'Needs Improvement'
    END as gitlab_reliability_rating,
    -- Performance comparison
    CASE
        WHEN system = 'Airflow' THEN null  -- First row
        ELSE
            CASE
                WHEN avg_duration_seconds < (SELECT avg_duration_seconds FROM base_metrics WHERE system = 'Airflow')
                THEN 'Better than Airflow'
                WHEN avg_duration_seconds > (SELECT avg_duration_seconds FROM base_metrics WHERE system = 'Airflow')
                THEN 'Worse than Airflow'
                ELSE 'Equal to Airflow'
            END
    END as performance_comparison
FROM base_metrics
ORDER BY system;
