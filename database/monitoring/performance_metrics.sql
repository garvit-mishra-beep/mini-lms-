-- MiniLMS Production Performance & Buffer Pool Monitoring
SELECT 
    VARIABLE_NAME, 
    VARIABLE_VALUE 
FROM performance_schema.global_status 
WHERE VARIABLE_NAME IN (
    'Innodb_buffer_pool_reads', 
    'Innodb_buffer_pool_read_requests', 
    'Queries', 
    'Threads_connected', 
    'Threads_running', 
    'Uptime'
);
