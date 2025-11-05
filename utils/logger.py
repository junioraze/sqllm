# 🔐 Configurar Google Auth PRIMEIRO (antes de google.cloud)
from config import google_auth

from google.cloud import bigquery
from datetime import datetime
import uuid
import json
import os
from config.settings import DATASET_LOG_ID, CLIENTE_NAME, MAX_RATE_LIMIT

client = bigquery.Client()

def log_interaction(
    user_input,
    function_params,
    query,
    raw_data,
    raw_response=None,
    refined_response=None,
    first_ten_table_lines=None,
    graph_data=None,
    export_data=None,
    status="OK",
    status_msg=None,
    error=None,
    session_id=None,
    client_request_count=None,
    custom_fields=None,
):
    """
    Insere um registro de log na tabela de log do BigQuery, mapeando para o schema correto.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    now = datetime.now()
    date_input = now.strftime("%Y-%m-%d")
    hour_minute_input = now.strftime("%H:%M")

    # Prepara os campos do struct log_metadata
    log_metadata = {
        "date_input": date_input,
        "hour_minute_input": hour_minute_input,
        "question": user_input,
        "raw_response": json.dumps(raw_response) if raw_response else "",
        "refined_response": refined_response if refined_response else "",
        "function_params": json.dumps(function_params, default=str) if function_params else None,
        "sql_query": query,
        "first_ten_table_lines": json.dumps(first_ten_table_lines, default=str) if first_ten_table_lines else (
            json.dumps(raw_data[:10], default=str) if raw_data else None
        ),
        "graph_data": json.dumps(graph_data, default=str) if graph_data else None,
        "export_data": json.dumps(export_data, default=str) if export_data else None,
        "client_max_request": MAX_RATE_LIMIT,
        "client_request_count": client_request_count if client_request_count is not None else None,
        "status_msg": status_msg if status_msg else (str(error) if error else None),
        "custom_fields": json.dumps(custom_fields, default=str) if custom_fields else None,
    }

    # Prepara o backup completo
    full_payload = json.dumps({
        "user_input": user_input,
        "function_params": function_params,
        "query": query,
        "raw_data": raw_data,
        "raw_response": raw_response,
        "refined_response": refined_response,
        "first_ten_table_lines": first_ten_table_lines,
        "graph_data": graph_data,
        "export_data": export_data,
        "status": status,
        "status_msg": status_msg,
        "error": error,
        "client_request_count": client_request_count,
        "custom_fields": custom_fields,
        "timestamp": now.isoformat(),
    }, default=str)

    row = {
        "client_id": CLIENTE_NAME,
        "status": "ERROR" if error else status,
        "log_metadata": log_metadata,
        "full_payload": full_payload,
    }

    errors = client.insert_rows_json(DATASET_LOG_ID, [row])
    if errors:
        print("Erro ao inserir log:", errors)