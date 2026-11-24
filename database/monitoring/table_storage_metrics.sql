-- MiniLMS Table Storage & Index Size Metrics
SELECT 
    table_name AS `Table`,
    ROUND(((data_length + index_length) / 1024 / 1024), 3) AS `Total_MB`,
    ROUND((data_length / 1024 / 1024), 3) AS `Data_MB`,
    ROUND((index_length / 1024 / 1024), 3) AS `Index_MB`,
    table_rows AS `Rows`
FROM information_schema.TABLES
WHERE table_schema = 'minilms_db'
ORDER BY (data_length + index_length) DESC;
