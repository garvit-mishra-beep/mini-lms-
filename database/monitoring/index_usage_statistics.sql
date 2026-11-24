-- MiniLMS Index Usage & Redundancy Analysis
SELECT 
    OBJECT_SCHEMA, 
    OBJECT_NAME, 
    INDEX_NAME, 
    COUNT_FETCH, 
    COUNT_INSERT, 
    COUNT_UPDATE, 
    COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'minilms_db'
ORDER BY COUNT_FETCH DESC;
