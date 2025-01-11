WITH time_intervals AS (
  SELECT generate_series(
    $__timeFrom(),
    $__timeTo(),
    '1 minute'::interval
  ) AS interval_start
),
running_dags AS (
  SELECT
    date_trunc('minute', t) AS time_bucket,
    COUNT(DISTINCT dag_id) as concurrent_dags
  FROM (
    SELECT
      dag_id,
      generate_series(
        execution_date + INTERVAL '1 hour',  -- Added 1 hour adjustment
        (execution_date + INTERVAL '1 second' * run_duration) + INTERVAL '1 hour',  -- Added 1 hour adjustment
        '1 minute'
      ) as t
    FROM thesis_airflow_dag_runs
    WHERE execution_date BETWEEN $__timeFrom() AND $__timeTo()
    AND state = 'success'
  ) ts
  GROUP BY date_trunc('minute', t)
),
running_jobs AS (
  SELECT
    date_trunc('minute', t) AS time_bucket,
    COUNT(DISTINCT job_name) as concurrent_jobs
  FROM (
    SELECT
      job_name,
      generate_series(
        start_time,
        start_time + INTERVAL '1 second' * total_duration_seconds,
        '1 minute'
      ) as t
    FROM thesis_jenkins_builds
    WHERE start_time BETWEEN $__timeFrom() AND $__timeTo()
    AND build_status IN ('SUCCESS', 'UNSTABLE')
  ) ts
  GROUP BY date_trunc('minute', t)
)
SELECT
  i.interval_start as time,
  COALESCE(rd.concurrent_dags, 0) as "Airflow Concurrent DAGs",
  COALESCE(rj.concurrent_jobs, 0) as "Jenkins Concurrent Jobs"
FROM time_intervals i
LEFT JOIN running_dags rd ON i.interval_start = rd.time_bucket
LEFT JOIN running_jobs rj ON i.interval_start = rj.time_bucket
ORDER BY time;