CREATE OR REPLACE TABLE `glinhares.teste.LogsVQ` (
  -- Controle (particionamento/clusterização)
  insert_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  client_id STRING,
  status STRING,  -- "OK", "ERROR" (filtro comum)
  
  -- Dados principais (STRUCT para organização e performance)
  log_metadata STRUCT<
    -- Campos básicos (sempre preenchidos)
    date_input STRING,
    hour_minute_input STRING,
    question STRING,
    raw_response STRING,
    refined_response STRING,
    
    -- Dados de execução
    function_params STRING,  -- JSON serializado
    sql_query STRING,
    
    -- Resultados (JSON para flexibilidade)
    first_ten_table_lines STRING,
    graph_data STRING,
    export_data STRING,
    
    -- Controle de requisições
    client_max_request INT64,
    client_request_count INT64,
    status_msg STRING,
    
    -- Campos adicionais dinâmicos
    custom_fields STRING  -- JSON serializado
  >,
  
  -- Backup completo (para treinamento de modelos)
  full_payload STRING
)
PARTITION BY DATE(insert_timestamp)  -- Filtro por data
CLUSTER BY client_id, status;  -- Otimiza consultas por cliente/status