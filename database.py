from google.cloud import bigquery
from config import FULL_TABLE_ID

client = bigquery.Client()

def execute_query(query: str):
    """Executa uma query SQL no BigQuery."""
    try:
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000)
        query_job = client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        return {"error": str(e), "query": query}

def build_query(params: dict) -> str:
    """
    Constrói a query exatamente conforme os parâmetros recebidos
    sem manipulações automáticas
    """
    # Validação robusta do parâmetro 'select'
    select = params.get("select", ["*"])
    if isinstance(select, str):
        if select.startswith("[") and select.endswith("]"):
            select = [item.strip().strip('"').strip("'") for item in select[1:-1].split(",")]
        else:
            select = [select.strip()]
    
    # Validação QUALIFY vs LIMIT
    if params.get("qualify") and params.get("limit"):
        raise ValueError("NUNCA use LIMIT com QUALIFY - use QUALIFY para múltiplas dimensões")

    where = f" WHERE {params['where']}" if params.get("where") else ""
    group_by = f" GROUP BY {', '.join(params['group_by'])}" if params.get("group_by") else ""
    order_by = f" ORDER BY {', '.join(params['order_by'])}" if params.get("order_by") else ""
    qualify = f" QUALIFY {params['qualify']}" if params.get("qualify") else ""
    limit = f" LIMIT {int(params['limit'])}" if params.get("limit") else ""

    query = f"""
        SELECT {', '.join(select)}
        FROM `{FULL_TABLE_ID}`
        {where}
        {group_by}
        {qualify}
        {order_by}
        {limit}
    """
    return query.strip()