from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID

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
        if param.startswith("[") and param.endswith("]"):
            # String que parece lista: "['item1', 'item2']"
            # Parse inteligente que respeita parênteses e aspas
            result = []
            content = param[1:-1]  # Remove [ e ]
            
            # Split inteligente que respeita parênteses e aspas aninhadas
            parts = []
            current_part = ""
            paren_count = 0
            quote_count = 0
            in_single_quote = False
            in_double_quote = False
            
            i = 0
            while i < len(content):
                char = content[i]
                
                # Controla estado das aspas
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                
                # Controla parênteses apenas fora de aspas
                elif not in_single_quote and not in_double_quote:
                    if char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
                    elif char == "," and paren_count == 0:
                        # Vírgula fora de parênteses - fim do item
                        parts.append(current_part.strip())
                        current_part = ""
                        i += 1
                        continue
                
                current_part += char
                i += 1
            
            # Adiciona último item
            if current_part.strip():
                parts.append(current_part.strip())
            
            # Limpa cada parte
            for part in parts:
                cleaned = part.strip().strip('"').strip("'")
                if cleaned:
                    result.append(cleaned)
        else:
            # String simples: "item1"
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
    """
    Constrói a query exatamente conforme os parâmetros recebidos
    O full_table_id já vem completo do Gemini
    ATUALIZADO: Suporte a CTEs (Common Table Expressions) para queries complexas
    """
    # Aplica correções automáticas nos parâmetros
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

    # Suporte a CTE (Common Table Expressions)
    with_clause = ""
    if corrected_params.get("with_cte"):
        with_clause = f"WITH {corrected_params['with_cte']}\n"
    
    # Determina a tabela a usar (pode ser uma CTE ou tabela física)
    from_table = corrected_params.get("from_table", f"`{full_table_id}`")

    # Constrói as partes da query
    where = f" WHERE {corrected_params['where']}" if corrected_params.get("where") else ""
    group_by = f" GROUP BY {', '.join(group_by_list)}" if group_by_list else ""
    order_by = f" ORDER BY {', '.join(order_by_list)}" if order_by_list else ""
    qualify = f" QUALIFY {corrected_params['qualify']}" if corrected_params.get("qualify") else ""
    limit = f" LIMIT {int(corrected_params['limit'])}" if corrected_params.get("limit") else ""

    query = f"""{with_clause}SELECT {', '.join(select)}
FROM {from_table}{where}{group_by}{qualify}{order_by}{limit}"""
    
    print(f"DEBUG - Query construída:\n{query}")
    return query.strip()