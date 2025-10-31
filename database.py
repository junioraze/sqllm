
from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID
import ast
import re
import sqlparse
from config import TABLES_CONFIG

# Função para remover comentários SQL
def remove_sql_comments(query: str) -> str:
    # Remove comentários de bloco /* ... */
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    # Remove comentários de linha -- ...
    query = re.sub(r'--.*?(\n|$)', '', query)
    return query

client = bigquery.Client()

def fix_sql_issues(query):
    """Função simplificada de correção SQL: remove comentários"""
    query = remove_sql_comments(query)
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


def validate_sql_query(query: str) -> dict:
    """Valida sintaxe SQL usando sqlparse."""
    try:
        parsed = sqlparse.parse(query)
        if not parsed or not parsed[0].tokens:
            return {"valid": False, "error": "Query vazia ou inválida."}
        # Pode adicionar mais regras de validação aqui
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def execute_query(query: str):
    """Executa uma query SQL no BigQuery, validando sintaxe antes."""
    # Aplica correções automáticas de SQL
    original_query = query
    corrected_query = fix_sql_issues(query)

    # Log das correções aplicadas
    if original_query != corrected_query:
        log_sql_correction(original_query, corrected_query, "execute_query")



    # Validação de sintaxe local
    validation = validate_sql_query(corrected_query)
    if not validation["valid"]:
        print(f"ERRO SINTAXE SQL: {validation['error']}")
        print(f"SQL gerado com erro:\n{corrected_query}")
        raise ValueError(f"Erro de sintaxe SQL: {validation['error']}\nSQL: {corrected_query}")

    # Validação extra: hífen fora de nomes de tabela/alias (concatenação errada)
    # Exemplo: ...ecPedidosVenda`-public-data...
    hyphen_pattern = r"`-[\w\-\.]+`"
    if re.search(hyphen_pattern, corrected_query):
        print(f"ERRO DE CONCATENAÇÃO: hífen '-' fora de nomes de tabela/alias detectado.")
        print(f"SQL gerado com erro:\n{corrected_query}")
        raise ValueError(f"Erro de concatenação: hífen '-' fora de nomes de tabela/alias detectado.\nSQL: {corrected_query}")

    try:
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
        print(f"SQL gerado com erro:\n{corrected_query}")
        return {
            "error": str(e),
            "query": corrected_query
        }

def build_query(params: dict) -> str:
    # Apenas constrói a query fielmente conforme os parâmetros recebidos
    original_params = params.copy()
    corrected_params = fix_function_params(params)

    # Log das correções nos parâmetros
    if original_params != corrected_params:
        print(f"PARAM_CORRECTION: {original_params} -> {corrected_params}")

    # Debug: log dos parâmetros corrigidos
    print(f"DEBUG - Parâmetros recebidos no build_query: {corrected_params}")

    # Novo padrão: referência de tabela sempre extraída do FROM da primeira CTE
    def extract_table_from_cte(cte):
        """Extrai o nome da tabela original do FROM da primeira CTE."""
        match = re.search(r"FROM\s+([`\w\.]+)", cte, re.IGNORECASE)
        if match:
            return match.group(1).replace('`', '').strip()
        return None


    def clean_cte_block(cte: str) -> str:
        """
        Remove o SELECT final embutido do campo CTE, deixando só as definições das CTEs.
        """
        # Busca o fechamento da última CTE (último ')')
        last_close = cte.rfind(')')
        if last_close != -1:
            after = cte[last_close+1:].strip()
            if after.upper().startswith('SELECT'):
                return cte[:last_close+1]
        return cte

    cte = corrected_params.get("cte", "")
    cte = clean_cte_block(cte)
    table_name_in_cte = extract_table_from_cte(cte)
    if table_name_in_cte and table_name_in_cte in TABLES_CONFIG:
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name_in_cte}"
    else:
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{list(TABLES_CONFIG.keys())[0]}"

    select = _parse_list_param(corrected_params.get("select", ["*"]), "select")
    order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
    temporal_fields = [f for f in select if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
    temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
    for tf in temporal_fields:
        if tf not in order_by:
            order_by.append(tf)
    if not select:
        select = ["*"]

    with_clause = ""
    query = ""
    from_table = corrected_params.get('from_table', '').strip()

    if cte:
        cte_clean = cte.strip()
        if cte_clean.upper().startswith("WITH "):
            cte_clean = cte_clean[5:].lstrip()
        with_clause = f"WITH {cte_clean}\n"

        # NOVO: se from_table contém expressão complexa (JOIN, ON, etc), não modificar
        if not from_table:
            raise ValueError("O parâmetro 'from_table' deve ser o alias de uma CTE gerada pelo modelo ou expressão de JOIN. Nenhum valor foi fornecido.")
        if any(x in from_table.upper() for x in ["JOIN", " ON ", " AS "]):
            pass  # usa como está
        elif from_table in TABLES_CONFIG.keys():
            pass  # usa como está
        elif '.' in from_table:
            from_table = from_table.split('.')[-1].replace('`','').strip()
    else:
        if not from_table or not str(from_table).strip():
            from_table = correct_table_ref

    where = f" WHERE {corrected_params['where']}" if corrected_params.get("where") else ""
    select_final = []
    for s in select:
        if re.search(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(", s, re.IGNORECASE):
            m = re.search(r"AS\s+(\w+)$", s, re.IGNORECASE)
            if m:
                select_final.append(m.group(1).strip())
        else:
            select_final.append(s)
    if not order_by:
        temporal_fields = [f for f in select_final if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
        temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
        for tf in temporal_fields:
            if tf not in order_by:
                order_by.append(tf)
    order_by_sql = f" ORDER BY {', '.join(order_by)}" if order_by else ""
    limit = ""  # LIMIT descontinuado, ranking já é feito via window function/where

    where_clause = where
    if corrected_params.get("where") and "ranking <= " in corrected_params["where"]:
        pass
    elif corrected_params.get("ranking_filter"):
        if where_clause:
            where_clause += f" AND {corrected_params['ranking_filter']}"
        else:
            where_clause = f" WHERE {corrected_params['ranking_filter']}"

    # Monta query principal, usando from_table como está (pode ser JOIN)
    query = f"{with_clause}SELECT {', '.join(select_final)} FROM {from_table}{where_clause}{order_by_sql}"

    query_clean = re.sub(r'[\n\t]+', ' ', query)
    query_clean = re.sub(r' +', ' ', query_clean)

    query_no_comments = remove_sql_comments(query_clean.strip())
    print(f"DEBUG - Query construída:\n{query_no_comments}")
    return query_no_comments