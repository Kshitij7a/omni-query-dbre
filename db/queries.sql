-- db/queries.sql

-- Find top slow queries utilizing excessive execution time
SELECT 
    queryid,
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
WHERE calls > 50 AND mean_exec_time > 10.0
ORDER BY total_exec_time DESC
LIMIT 50;

-- Identify tables with many sequential scans (potential missing index)
SELECT 
    relname AS table_name,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 100 AND seq_tup_read > 100000
ORDER BY seq_tup_read DESC
LIMIT 50;
