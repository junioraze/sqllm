from google.cloud import bigquery
from config import FULL_TABLE_ID

client = bigquery.Client()

def execute_query(query: str):
    """
    Executa uma query SQL no BigQuery e retorna os resultados como lista de dicionários.
    Em caso de erro, retorna um dicionário com a chave 'error'.
    """
    try:
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000)
        query_job = client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        return {"error": str(e), "query": query}

def build_query(params: dict) -> str:
    """
    Constrói uma query SQL a partir dos parâmetros fornecidos pelo modelo.
    Espera os campos: select, where, group_by, order_by, limit.
    """
    select = ", ".join(params.get("select", ["*"]))
    where = f" WHERE {params['where']}" if "where" in params and params["where"] else ""
    group_by = f" GROUP BY {', '.join(params['group_by'])}" if "group_by" in params and params["group_by"] else ""
    order_by = f" ORDER BY {', '.join(params['order_by'])}" if "order_by" in params and params["order_by"] else ""
    limit = ""
    if "limit" in params and params["limit"]:
        try:
            limit = f" LIMIT {int(params['limit'])}"
        except (ValueError, TypeError):
            pass

    query = f"""
        SELECT {select}
        FROM `{FULL_TABLE_ID}`
        {where}
        {group_by}
        {order_by}
        {limit}
    """
    return query.strip()