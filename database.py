# 🔐 Configurar Google Auth PRIMEIRO (antes de google.cloud)
from config import google_auth

from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID
import ast
import re
import sqlparse
import pandas as pd
from config import TABLES_CONFIG
from database.validator import QueryValidator, validate_and_build_query

# Função para remover comentários SQL
def remove_sql_comments(query: str) -> str:
    # Remove comentários de bloco /* ... */
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    # Remove comentários de linha -- ...
    query = re.sub(r'--.*?(\n|$)', '', query)
    return query

client = bigquery.Client(project=PROJECT_ID)
query_validator = QueryValidator(max_retries=2)

def sort_results_by_columns(results):
    """
    Ordena resultados por colunas prioritárias para garantir consistência em gráficos.
    
    Prioridade:
    1. Colunas com data/período (mes, ano, data, date, timestamp, etc)
    2. Colunas numéricas após ordenadas por data
    3. Resto dos dados
    
    Args:
        results: list de dicts ou DataFrame
        
    Returns:
        DataFrame ordenado ou list de dicts
    """
    if not results:
        return results
    
    # Converte para DataFrame se for lista
    if isinstance(results, list):
        df = pd.DataFrame(results)
    else:
        df = results.copy()
    
    if df.empty:
        return results
    
    # Identifica colunas de data/período
    date_columns = []
    numeric_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        # Detecta colunas de data/período
        if any(x in col_lower for x in ['mes', 'ano', 'data', 'date', 'dia', 'mês', 'month', 'year', 'quarter', 'trimestre', 'semana', 'week', 'timestamp', 'time']):
            date_columns.append(col)
        # Detecta colunas numéricas
        elif df[col].dtype in ['int64', 'float64']:
            numeric_columns.append(col)
    
    # Ordena por colunas de data/período primeiro
    sort_cols = date_columns + numeric_columns
    if sort_cols:
        try:
            df = df.sort_values(by=sort_cols, ascending=True)
        except Exception as e:
            print(f"⚠️  Erro ao ordenar por {sort_cols}: {e}")
            pass
    
    # Converte de volta para list de dicts se entrada foi list
    if isinstance(results, list):
        return df.to_dict('records')
    return df

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

def execute_query(query: str, user_question: str = "", gemini_model = None, validate: bool = True):
    """
    Executa query SQL no BigQuery com VALIDAÇÃO + RETRY AUTOMÁTICO.
    
    Fluxo:
    1. Remove comentários SQL
    2. Valida sintaxe com sqlparse
    3. Se falhar, tenta refinar com Gemini (até 2 vezes)
    4. Só executa no BigQuery se query passar na validação
    
    Parâmetros:
    - query: SQL a executar
    - user_question: pergunta original do usuário (para refino)
    - gemini_model: modelo Gemini para refino automático
    - validate: se True, faz validação + retry; se False, executa direto
    
    Retorna: lista de resultados ou dict com erro
    """
    
    original_query = query
    
    # STEP 1: Remove comentários
    corrected_query = fix_sql_issues(query)
    
    if original_query != corrected_query:
        log_sql_correction(original_query, corrected_query, "execute_query")
    
    # STEP 2: VALIDAÇÃO + RETRY (novo pipeline)
    if validate and gemini_model:
        print("\n" + "="*70)
        print("[PIPELINE] VALIDAÇÃO + RETRY AUTOMÁTICO INICIADO")
        print("="*70)
        
        validation_result = query_validator.validate_and_refine(
            corrected_query,
            user_question,
            gemini_model
        )
        
        if validation_result["is_valid"]:
            corrected_query = validation_result["query"]
            print(f"\n✅ [PIPELINE] Query validada e pronta para BigQuery")
            print(f"   Tentativas: {validation_result['retry_count'] + 1}")
        else:
            print(f"\n❌ [PIPELINE] {validation_result.get('error_message', 'Erro desconhecido')}")
            print(f"   Erros finais: {validation_result.get('final_errors', [])}")
            return {
                "error": validation_result.get('error_message', 'Query não validada'),
                "query": corrected_query,
                "validation_history": validation_result.get('history', [])
            }
    else:
        # Se validate=False, apenas faz validação básica (backward compatibility)
        validation = validate_sql_query(corrected_query)
        if not validation["valid"]:
            print(f"ERRO SINTAXE SQL: {validation['error']}")
            print(f"SQL gerado com erro:\n{corrected_query}")
            raise ValueError(f"Erro de sintaxe SQL: {validation['error']}\nSQL: {corrected_query}")
    
    # STEP 3: Validação extra: hífen fora de nomes de tabela/alias
    hyphen_pattern = r"`-[\w\-\.]+`"
    if re.search(hyphen_pattern, corrected_query):
        print(f"ERRO DE CONCATENAÇÃO: hífen '-' fora de nomes de tabela/alias detectado.")
        print(f"SQL gerado com erro:\n{corrected_query}")
        raise ValueError(f"Erro de concatenação: hífen '-' fora de nomes de tabela/alias detectado.\nSQL: {corrected_query}")

    # STEP 4: Executa no BigQuery
    try:
        print(f"\n[BIGQUERY] Executando query no BigQuery...")
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=100_000_000,
            job_timeout_ms=30000  # 30 segundos timeout
        )
        query_job = client.query(corrected_query, job_config=job_config)

        # Executa e converte resultados
        results = []
        for row in query_job.result(timeout=30):
            results.append(dict(row))

        print(f"✅ [BIGQUERY] Query executada com sucesso. {len(results)} linhas retornadas.")
        
        # 🔥 ORDENA RESULTADOS SEMPRE (importante para gráficos com datas)
        results = sort_results_by_columns(results)
        
        return results

    except Exception as e:
        print(f"❌ [BIGQUERY] ERRO: {str(e)}")
        print(f"SQL com erro:\n{corrected_query}")
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

    cte = corrected_params.get("cte", "").strip()
    select = _parse_list_param(corrected_params.get("select", ["*"]), "select")
    order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
    
    # Verifica se a CTE já é uma query completa (contém SELECT final após as CTEs)
    def is_complete_query(cte_text):
        """Verifica se a CTE já inclui o SELECT final (query completa)"""
        if not cte_text:
            return False
        
        # Remove comentários para análise mais precisa
        clean_cte = remove_sql_comments(cte_text)
        clean_cte_upper = clean_cte.upper().strip()
        
        # Verificação simples: conta ocorrências de SELECT
        # Query COMPLETA tem pelo menos 2 SELECTs (1+ dentro de CTE + 1 final)
        # Query INCOMPLETA tem só 1 SELECT (dentro das CTEs)
        select_count = clean_cte_upper.count('SELECT')
        
        # Se tem apenas 1 SELECT, é uma query incompleta
        if select_count < 2:
            print(f"DEBUG - is_complete_query: Apenas {select_count} SELECT encontrado(s) - INCOMPLETA")
            return False
        
        # Verificação alternativa: procura pelo padrão "SELECT ... FROM"
        # que indica um SELECT final após as CTEs
        pattern_final_select = re.search(
            r'\)\s*SELECT\s+.*\s+FROM\s+\w+',
            clean_cte,
            re.IGNORECASE | re.DOTALL
        )
        
        is_complete = pattern_final_select is not None
        print(f"DEBUG - is_complete_query: pattern_final_select={pattern_final_select is not None} - {'COMPLETA' if is_complete else 'INCOMPLETA'}")
        return is_complete

    # SE a CTE já for uma query completa, usa ela diretamente
    if cte and is_complete_query(cte):
        print("DEBUG - CTE identificada como query completa, usando diretamente")
        query_clean = re.sub(r'[\n\t]+', ' ', cte)
        query_clean = re.sub(r' +', ' ', query_clean).strip()
        query_no_comments = remove_sql_comments(query_clean)
        print(f"DEBUG - Query completa retornada:\n{query_no_comments}")
        return query_no_comments

    # SE NÃO for query completa, faz a montagem padrão
    print("DEBUG - CTE não é query completa, fazendo montagem padrão")
    
    # Resto do código original para montagem padrão...
    def extract_table_from_cte(cte):
        """Extrai o nome da tabela original do FROM da primeira CTE."""
        match = re.search(r"FROM\s+([`\w\.]+)", cte, re.IGNORECASE)
        if match:
            return match.group(1).replace('`', '').strip()
        return None

    cte = corrected_params.get("cte", "")
    table_name_in_cte = extract_table_from_cte(cte)
    if table_name_in_cte and table_name_in_cte in TABLES_CONFIG:
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name_in_cte}"
    else:
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{list(TABLES_CONFIG.keys())[0]}"

    bq_table_pattern = re.compile(rf"{PROJECT_ID}\.{DATASET_ID}\.(\w+)")
    match_bq_table = bq_table_pattern.search(table_name_in_cte or "")
    if match_bq_table:
        table_base = match_bq_table.group(1)
        if table_base in TABLES_CONFIG.keys():
            expected_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_base}"
            # 🔥 FIX: Usar count=1 para substituir apenas o PRIMEIRO FROM (o principal)
            # Evita substituir FROM dentro de EXTRACT(), CAST(), etc
            cte = re.sub(rf"FROM\s+([`\w\.]+)", f"FROM `{expected_ref}`", cte, flags=re.IGNORECASE, count=1)
            corrected_params["cte"] = cte

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
        is_full_query = False
        cte_upper = cte.strip().upper()
        if cte_upper.startswith("WITH"):
            par_count = 0
            last_select_pos = -1
            for i, char in enumerate(cte):
                if char == '(': par_count += 1
                elif char == ')': par_count -= 1
                if cte[i:i+6].upper() == 'SELECT' and par_count == 0:
                    last_select_pos = i
            if last_select_pos != -1:
                is_full_query = True
        if is_full_query:
            query_clean = re.sub(r'[\n\t]+', ' ', cte)
            query_clean = re.sub(r' +', ' ', query_clean)
            order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
            if order_by:
                order_by_clause = f" ORDER BY {', '.join(order_by)}"
                if "ORDER BY" not in query_clean.upper():
                    query_clean = query_clean.strip()
                    query_clean += order_by_clause
            print(f"DEBUG - Query construída:\n{query_clean}")
            return query_clean.strip()
        else:
            with_clause = f"WITH {cte_clean}\n"

        # NOVO: se from_table contém expressão complexa (JOIN, ON, etc), não modificar
        if not from_table:
            raise ValueError("O parâmetro 'from_table' deve ser o alias de uma CTE gerada pelo modelo ou expressão de JOIN. Nenhum valor foi fornecido.")
        # Se for JOIN ou expressão complexa, usa como está
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
    limit = f" LIMIT {int(corrected_params['limit'])}" if corrected_params.get("limit") else ""

    where_clause = where
    if corrected_params.get("where") and "ranking <= " in corrected_params["where"]:
        pass
    elif corrected_params.get("ranking_filter"):
        if where_clause:
            where_clause += f" AND {corrected_params['ranking_filter']}"
        else:
            where_clause = f" WHERE {corrected_params['ranking_filter']}"

    # Monta query principal, usando from_table como está (pode ser JOIN)
    query = f"{with_clause}SELECT {', '.join(select_final)} FROM {from_table}{where_clause}{order_by_sql}{limit}"

    query_clean = re.sub(r'[\n\t]+', ' ', query)
    query_clean = re.sub(r' +', ' ', query_clean)

    query_no_comments = remove_sql_comments(query_clean.strip())
    print(f"DEBUG - Query construída:\n{query_no_comments}")
    return query_no_comments