from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID

client = bigquery.Client()

def _parse_list_param(param, param_name="param"):
    """
    Converte parâmetro que pode ser string ou lista em lista limpa.
    Trata casos como: "['item1', 'item2']" ou ['item1', 'item2'] ou "item1"
    """
    if not param:
        return []
    
    print(f"DEBUG - {param_name} inicial: {param} (tipo: {type(param)})")
    
    if isinstance(param, str):
        if param.startswith("[") and param.endswith("]"):
            # String que parece lista: "['item1', 'item2']"
            result = [
                item.strip().strip('"').strip("'") for item in param[1:-1].split(",")
                if item.strip().strip('"').strip("'")  # Remove itens vazios
            ]
        else:
            # String simples: "item1"
            result = [param.strip()]
    else:
        # Já é lista ou outro tipo
        result = list(param) if param else []
    
    # Filtra elementos vazios e espaços
    result = [item for item in result if item and str(item).strip()]
    
    print(f"DEBUG - {param_name} processado: {result}")
    return result

def execute_query(query: str):
    """Executa uma query SQL no BigQuery."""
    try:
        # Debug: log da query antes de executar
        print(f"DEBUG - Query a ser executada:\n{query}")
        
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000)
        query_job = client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        print(f"DEBUG - Erro na execução: {str(e)}")
        print(f"DEBUG - Query que falhou:\n{query}")
        return {"error": str(e), "query": query}

def build_query(params: dict) -> str:
    """
    Constrói a query exatamente conforme os parâmetros recebidos
    O full_table_id já vem completo do Gemini
    """
    # Debug: log dos parâmetros recebidos
    print(f"DEBUG - Parâmetros recebidos no build_query: {params}")
    
    full_table_id = params.get("full_table_id")
    if not full_table_id:
        raise ValueError("full_table_id é obrigatório")
    
    # Processa todos os parâmetros de lista usando a função auxiliar
    select = _parse_list_param(params.get("select", ["*"]), "select")
    group_by_list = _parse_list_param(params.get("group_by"), "group_by")
    order_by_list = _parse_list_param(params.get("order_by"), "order_by")
    
    # Garante que select não fique vazio
    if not select:
        select = ["*"]

    if params.get("qualify") and params.get("limit"):
        raise ValueError(
            "NUNCA use LIMIT com QUALIFY - use QUALIFY para múltiplas dimensões"
        )

    # Constrói as partes da query
    where = f" WHERE {params['where']}" if params.get("where") else ""
    group_by = f" GROUP BY {', '.join(group_by_list)}" if group_by_list else ""
    order_by = f" ORDER BY {', '.join(order_by_list)}" if order_by_list else ""
    qualify = f" QUALIFY {params['qualify']}" if params.get("qualify") else ""
    limit = f" LIMIT {int(params['limit'])}" if params.get("limit") else ""

    query = f"""
        SELECT {', '.join(select)}
        FROM `{full_table_id}`
        {where}
        {group_by}
        {qualify}
        {order_by}
        {limit}
    """
    
    print(f"DEBUG - Query construída:\n{query}")
    return query.strip()