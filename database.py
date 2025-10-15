from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID
import ast
import re

client = bigquery.Client()

def fix_sql_issues(query):
    """Função simplificada de correção SQL"""
    return query

def fix_function_params(params):
    """Função simplificada de correção de parâmetros"""
    return params

def log_sql_correction(original, corrected, correction_type):
    """Log simplificado - placeholder"""
    pass

def _parse_list_param(param, param_name="param"):
    """
    Converte parâmetro que pode ser string ou lista em lista limpa.
    Trata casos como: "['item1', 'item2']" ou ['item1', 'item2'] ou "item1"
    ATUALIZADO: Mantem integridade de funções SQL como FORMAT_DATE('%Y-%m', campo)
    """
    if not param:
        return []
    
    print(f"DEBUG - {param_name} inicial: {param} (tipo: {type(param)})")
    
    if isinstance(param, str):
        # Tenta avaliar como lista Python válida (caso venha como string de lista)
        try:
            parsed = ast.literal_eval(param)
            if isinstance(parsed, list):
                # Garante que cada item é string e não quebra SQL
                result = [str(item).strip() for item in parsed if str(item).strip()]
            else:
                result = [str(parsed).strip()]
        except Exception:
            # Fallback: trata como string simples
            result = [param.strip()]
    else:
        # Já é lista ou outro tipo
        result = list(param) if param else []
    
    # Filtra apenas elementos completamente vazios (mantém strings com conteúdo)
    result = [item for item in result if item and str(item).strip()]
    
    print(f"DEBUG - {param_name} processado: {result}")
    return result

def execute_query(query: str):
    """Executa uma query SQL no BigQuery."""
    try:
        # Aplica correções automáticas de SQL
        original_query = query
        corrected_query = fix_sql_issues(query)
        
        # Log das correções aplicadas
        if original_query != corrected_query:
            log_sql_correction(original_query, corrected_query, "execute_query")
        
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=100_000_000,
            job_timeout_ms=30000  # 30 segundos timeout
        )
        query_job = client.query(corrected_query, job_config=job_config)
        
        # Executa e converte resultados
        results = []
        for row in query_job.result(timeout=30):
            results.append(dict(row))
            
        return results
        
    except Exception as e:
        print(f"ERRO QUERY: {str(e)}")
        return {"error": str(e), "query": query}

def build_query(params: dict) -> str:
    # Apenas constrói a query fielmente conforme os parâmetros recebidos
    original_params = params.copy()
    corrected_params = fix_function_params(params)

    # Log das correções nos parâmetros
    if original_params != corrected_params:
        print(f"PARAM_CORRECTION: {original_params} -> {corrected_params}")

    # Debug: log dos parâmetros corrigidos
    print(f"DEBUG - Parâmetros recebidos no build_query: {corrected_params}")

    full_table_id = corrected_params.get("full_table_id")
    if not full_table_id:
        raise ValueError("full_table_id é obrigatório")
    # Sempre coloca o full_table_id entre crases para evitar problemas com '-' e outros caracteres
    if not (full_table_id.startswith('`') and full_table_id.endswith('`')):
        full_table_id = f'`{full_table_id}`'

    # Processa todos os parâmetros de lista usando a função auxiliar
    select = _parse_list_param(corrected_params.get("select", ["*"]), "select")
    group_by_list = _parse_list_param(corrected_params.get("group_by"), "group_by")
    order_by_list = _parse_list_param(corrected_params.get("order_by"), "order_by")

    # Garante que select não fique vazio
    if not select:
        select = ["*"]

    if corrected_params.get("qualify") and corrected_params.get("limit"):
        raise ValueError(
            "NUNCA use LIMIT com QUALIFY - use QUALIFY para múltiplas dimensões"
        )

    # Suporte a CTE (Common Table Expressions) - usa 'cte' se presente, sem duplicar 'WITH'
    with_clause = ""
    cte = corrected_params.get("cte")
    if cte:
        # Remove prefixo 'WITH' se vier por engano
        cte_clean = cte.strip()
        if cte_clean.upper().startswith("WITH "):
            cte_clean = cte_clean[5:].lstrip()
        with_clause = f"WITH {cte_clean}\n"

    # Caminho único: se não houver CTE, usa full_table_id como from_table automaticamente
    cte = corrected_params.get("cte")
    from_table = corrected_params.get("from_table")
    if cte:
        # Para queries com CTE, from_table é obrigatório e deve ser JOIN/alias
        if not from_table or not str(from_table).strip():
            raise ValueError("O parâmetro 'from_table' é obrigatório e deve ser passado explicitamente pelo modelo quando houver CTE. Nunca deduza ou use a tabela original por padrão. Veja o padrão RAG e a instrução do handler.")
    else:
        # Para queries simples, se from_table não vier, usa full_table_id
        if not from_table or not str(from_table).strip():
            from_table = full_table_id

    # Se o from_table for igual ao full_table_id sem crase, coloca crase
    if from_table == corrected_params.get("full_table_id") and not (from_table.startswith('`') and from_table.endswith('`')):
        from_table = f'`{from_table}`'

    # Constrói as partes da query fielmente conforme os parâmetros
    where = f" WHERE {corrected_params['where']}" if corrected_params.get("where") else ""
    group_by = f" GROUP BY {', '.join(group_by_list)}" if group_by_list else ""
    order_by = f" ORDER BY {', '.join(order_by_list)}" if order_by_list else ""
    qualify = f" QUALIFY {corrected_params['qualify']}" if corrected_params.get("qualify") else ""
    limit = f" LIMIT {int(corrected_params['limit'])}" if corrected_params.get("limit") else ""

    query = f"""{with_clause}SELECT {', '.join(select)}
FROM {from_table}{where}{group_by}{qualify}{order_by}{limit}"""

    # Remove \n, \t e espaços duplicados para evitar quebras
    query_clean = re.sub(r'[\n\t]+', ' ', query)
    query_clean = re.sub(r' +', ' ', query_clean)

    print(f"DEBUG - Query construída:\n{query_clean}")
    return query_clean.strip()