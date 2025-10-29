
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
    # Função utilitária para normalizar nome de tabela removendo crases
    def normalize_table_id(table_id):
        # Remove crase e espaços, para validação
        return table_id.replace('`', '').strip()

    def ensure_crase(table_id):
        # Garante crase ao redor do nome da tabela
        t = table_id.strip()
        if not (t.startswith('`') and t.endswith('`')):
            return f'`{t}`'
        return t

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

    cte = corrected_params.get("cte", "")
    table_name_in_cte = extract_table_from_cte(cte)
    # Monta referência correta do BigQuery
    if table_name_in_cte and table_name_in_cte in TABLES_CONFIG:
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name_in_cte}"
    else:
        # Se vier valor errado, tenta corrigir para a primeira tabela do config
        correct_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{list(TABLES_CONFIG.keys())[0]}"

    # Corrige o nome da tabela no CTE se necessário
    # Só substitui se for uma tabela do projeto/dataset do config
    # Só substitui se vier no padrão projeto.dataset.tabela
    bq_table_pattern = re.compile(rf"{PROJECT_ID}\.{DATASET_ID}\.(\w+)")
    match_bq_table = bq_table_pattern.search(table_name_in_cte or "")
    if match_bq_table:
        table_base = match_bq_table.group(1)
        if table_base in TABLES_CONFIG.keys():
            expected_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_base}"
            cte = re.sub(rf"FROM\s+([`\w\.]+)", f"FROM `{expected_ref}`", cte, flags=re.IGNORECASE)
            corrected_params["cte"] = cte


    # 1. Normaliza listas e corrige múltiplos agrupamentos
    select = _parse_list_param(corrected_params.get("select", ["*"]), "select")
    # group_by removido: agrupamento deve ocorrer apenas dentro do CTE
    order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
    # Garante ordenação do eixo X (data/temporal) no ORDER BY
    temporal_fields = [f for f in select if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
    temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
    for tf in temporal_fields:
        if tf not in order_by:
            order_by.append(tf)
    # Toda lógica de agrupamento depende apenas do CTE. Nenhum group_by externo é usado ou processado.

    # 3. Garante que select não fique vazio
    if not select:
        select = ["*"]


    # 4. Suporte a CTE (Common Table Expressions) - usa 'cte' se presente, sem duplicar 'WITH'
    with_clause = ""
    query = ""
    if cte:
        cte_clean = cte.strip()
        if cte_clean.upper().startswith("WITH "):
            cte_clean = cte_clean[5:].lstrip()
        # Só retorna o bloco do CTE se ele for uma query completa (WITH ... SELECT ...), ou seja, se o parâmetro for uma query final e não apenas CTEs
        # Só retorna o bloco do CTE se ele for uma query completa (WITH ... SELECT ... GROUP BY ...) e não apenas CTEs
        is_full_query = False
        cte_upper = cte.strip().upper()
        if cte_upper.startswith("WITH"):
            # Verifica se há apenas CTEs ou se há um SELECT principal após o bloco WITH
            # Considera query completa apenas se o último SELECT vier após o bloco de CTEs
            # Busca o último SELECT e verifica se ele está fora dos parênteses das CTEs
            par_count = 0
            last_select_pos = -1
            for i, char in enumerate(cte):
                if char == '(': par_count += 1
                elif char == ')': par_count -= 1
                if cte[i:i+6].upper() == 'SELECT' and par_count == 0:
                    last_select_pos = i
            # Se o último SELECT está fora dos parênteses das CTEs, é uma query completa
            if last_select_pos != -1:
                is_full_query = True
        if is_full_query:
            query_clean = re.sub(r'[\n\t]+', ' ', cte)
            query_clean = re.sub(r' +', ' ', query_clean)
            # Adiciona ORDER BY apenas ao SELECT final, nunca dentro de CTEs
            order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
            if order_by:
                order_by_clause = f" ORDER BY {', '.join(order_by)}"
                # Só adiciona ORDER BY se não existir e apenas ao final da query
                if "ORDER BY" not in query_clean.upper():
                    query_clean = query_clean.strip()
                    query_clean += order_by_clause
            print(f"DEBUG - Query construída:\n{query_clean}")
            return query_clean.strip()
        else:
            with_clause = f"WITH {cte_clean}\n"

        # Não exige mais o parâmetro 'from_table' explicitamente quando houver CTE; referência é extraída do CTE.
        # O from_table no SELECT final deve ser sempre um alias de CTE, nunca referência de tabela completa
        from_table = corrected_params.get('from_table', '').strip()
        # Se vier vazio, erro explícito
        if not from_table:
            raise ValueError("O parâmetro 'from_table' deve ser o alias de uma CTE gerada pelo modelo. Nenhum alias foi fornecido.")
        # Se vier nome de tabela completa, converte para alias
        if from_table in TABLES_CONFIG.keys():
            # Assume que existe uma CTE com esse nome
            pass
        elif '.' in from_table:
            # Se vier nome completo, pega só o alias
            from_table = from_table.split('.')[-1].replace('`','').strip()
    else:
        if not from_table or not str(from_table).strip():
            from_table = correct_table_ref
    # from_table já definido pelo padrão novo, não depende mais de full_table_id

    # 6. Monta demais cláusulas
    where = f" WHERE {corrected_params['where']}" if corrected_params.get("where") else ""
    # O SELECT final nunca deve ter GROUP BY ou agregação, apenas projeção dos campos já agregados/agrupados definidos nas CTEs
    # Remove agregações do SELECT final
    select_final = []
    for s in select:
        # Se for agregação (SUM, COUNT, AVG, etc), só inclui se vier como campo já definido (ex: quantidade)
        if re.search(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(", s, re.IGNORECASE):
            # Tenta extrair alias
            m = re.search(r"AS\s+(\w+)$", s, re.IGNORECASE)
            if m:
                select_final.append(m.group(1).strip())
            # Se não tem alias, ignora agregação no SELECT final
        else:
            select_final.append(s)
    # Remove GROUP BY do SELECT final
    # group_by_sql removido
    # Garante que todos os campos do eixo X e do parâmetro order_by estejam presentes
    if not order_by:
        temporal_fields = [f for f in select_final if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
        temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
        for tf in temporal_fields:
            if tf not in order_by:
                order_by.append(tf)
    order_by_sql = f" ORDER BY {', '.join(order_by)}" if order_by else ""
    limit = f" LIMIT {int(corrected_params['limit'])}" if corrected_params.get("limit") else ""

    # Se vier filtro de ranking, inclua no WHERE
    where_clause = where
    if corrected_params.get("where") and "ranking <= " in corrected_params["where"]:
        # Já está no WHERE
        pass
    elif corrected_params.get("ranking_filter"):
        # Se vier ranking_filter separado, inclua no WHERE
        if where_clause:
            where_clause += f" AND {corrected_params['ranking_filter']}"
        else:
            where_clause = f" WHERE {corrected_params['ranking_filter']}"

    # Monta query principal sem GROUP BY/agregação no SELECT final
    query = f"{with_clause}SELECT {', '.join(select_final)} FROM {from_table}{where_clause}{order_by_sql}{limit}"

    # 8. Remove espaços
    query_clean = re.sub(r'[\n\t]+', ' ', query)
    query_clean = re.sub(r' +', ' ', query_clean)

    # 9. Remove comentários SQL antes de retornar e logar
    query_no_comments = remove_sql_comments(query_clean.strip())
    print(f"DEBUG - Query construída:\n{query_no_comments}")
    return query_no_comments