# database.py
from google.cloud import bigquery
from config import FULL_TABLE_ID
import re

client = bigquery.Client()

def execute_query(query: str):
    """Executa a query no BigQuery e retorna os resultados."""
    try:
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=100000000)
        query_job = client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        return {"error": str(e), "query": query}

def build_query(params: dict) -> str:
    """Constrói query SQL com base nos parâmetros recebidos."""
    select = ", ".join(params.get("select", ["*"]))
    where = f" WHERE {params['where']}" if "where" in params else ""
    group_by = f" GROUP BY {', '.join(params['group_by'])}" if "group_by" in params else ""
    order_by = f" ORDER BY {', '.join(params['order_by'])}" if "order_by" in params else ""
    limit = ""
    if "limit" in params:
        try:
            limit = f" LIMIT {int(params['limit'])}"  # Força conversão para inteiro
        except (ValueError, TypeError):
            pass  # Ignora se não for conversível para inteiro
    

    query = f"""
        SELECT {select}
        FROM `{FULL_TABLE_ID}`
        {where}
        {group_by}
        {order_by}
        {limit}
    """
    
    return query.strip()