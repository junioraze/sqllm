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


    # 1. Normaliza listas e corrige múltiplos agrupamentos
    select = _parse_list_param(corrected_params.get("select", ["*"]), "select")
    group_by = _parse_list_param(corrected_params.get("group_by"), "group_by")
    order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
    # Garante ordenação do eixo X (data/temporal) no ORDER BY
    temporal_fields = [f for f in select if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
    # Extrai nome do campo (remove alias)
    temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
    for tf in temporal_fields:
        if tf not in order_by:
            order_by.append(tf)

    # 2. Corrige múltiplos agrupamentos e dimensões
    def get_non_agg_fields(select_list):
        fields = []
        for sel in select_list:
            if re.search(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(", sel, re.IGNORECASE):
                continue
            m = re.search(r"^([\w\.]+)(\s+AS\s+([\w\.]+))?", sel, re.IGNORECASE)
            if m:
                field = m.group(1)
                fields.append(field)
        return fields

    join_dims = set()
    from_table = corrected_params.get("from_table")
    if from_table:
        join_matches = re.findall(r"ON\s+([\w\.]+)\s*=\s*([\w\.]+)", str(from_table), re.IGNORECASE)
        for left, right in join_matches:
            join_dims.add(left)
            join_dims.add(right)

    cte_fields = set()
    cte = corrected_params.get("cte")
    if cte:
        cte_blocks = re.findall(r"(SELECT[\s\S]+?)(?:\)|$)", cte, re.IGNORECASE)
        if cte_blocks:
            last_cte_select = cte_blocks[-1]
            select_matches = re.findall(r"SELECT\s+([\w\.,\s]+)\s+FROM", last_cte_select, re.IGNORECASE)
            if select_matches:
                for match in select_matches:
                    for field in match.split(','):
                        field = field.strip()
                        if not re.search(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(", field, re.IGNORECASE):
                            field = field.split(' AS ')[0].strip()
                            cte_fields.add(field)

    has_agg = any(re.search(r"(SUM|COUNT|AVG|MIN|MAX)\s*\(", sel, re.IGNORECASE) for sel in select)
    # Extrai campos não agregados da última CTE utilizada como base
    last_cte_fields = set()
    if cte:
        # Busca a última CTE (usada como base)
        cte_blocks = re.findall(r"(\w+)\s+AS\s*\(([^)]*)\)", cte, re.IGNORECASE)
        if cte_blocks:
            last_cte_name, last_cte_sql = cte_blocks[-1]
            # Extrai campos do SELECT da última CTE (inclui prefixos, ignora agregados)
            select_match = re.search(r"SELECT\s+([\w\.,' %\-]+)\s+FROM", last_cte_sql, re.IGNORECASE)
            if select_match:
                for field in select_match.group(1).split(','):
                    field = field.strip()
                    if not re.search(r"(SUM|COUNT|AVG|MIN|MAX|COUNT\s*\()", field, re.IGNORECASE):
                        # Remove alias, preserva prefixo
                        field = field.split(' AS ')[0].strip()
                        last_cte_fields.add(field)
            # Também busca campos com prefixo (ex: t1.Pessoa) e sem alias
            select_prefix_match = re.findall(r"(\w+\.\w+)", last_cte_sql)
            for field in select_prefix_match:
                if not re.search(r"(SUM|COUNT|AVG|MIN|MAX|COUNT\s*\()", field, re.IGNORECASE):
                    last_cte_fields.add(field)

    # Lista de campos válidos (deve ser parametrizada ou extraída do meta, aqui hardcoded para exemplo)
    valid_fields = set([
        "Data", "Hora", "Pessoa", "Mensagem", "DataLastValue", "DataLookupPrevious", "PessoaLastValue", "DataHoraD", "Assunto", "Intencao", "Entidades", "Sentimento", "AcaoSugerida", "MessageWordCount", "TimeDiff", "DataRank", "MessagenLen"
    ])
    # Inclui todos os campos de categorização (dimensões não agregadas, JOIN, CTE, última CTE base) no SELECT e GROUP BY, filtrando apenas campos válidos
    required_fields = (set(get_non_agg_fields(select)) | join_dims | cte_fields | set(group_by) | last_cte_fields)
    required_fields = set([f for f in required_fields if f.split('.')[-1] in valid_fields])
    filtered_group_by = list(dict.fromkeys([g for g in group_by if g in required_fields]))
    for f in required_fields:
        if f not in filtered_group_by:
            print(f"[CORREÇÃO GROUP_BY] Adicionando campo obrigatório ao group_by: {f}")
            filtered_group_by.append(f)
    select_fields = set(get_non_agg_fields(select))
    for f in required_fields:
        if f not in select_fields:
            print(f"[CORREÇÃO SELECT] Adicionando campo não agregado ao SELECT: {f}")
            alias = f.split('.')[-1]
            select.append(f + f' AS {alias}')
    # Remove duplicidade no SELECT
    select = list(dict.fromkeys(select))
    if not has_agg and filtered_group_by:
        print("[CORREÇÃO GROUP_BY] Removendo todos os campos do group_by pois SELECT final não tem agregação.")
        filtered_group_by = []

    # 3. Garante que select não fique vazio
    if not select:
        select = ["*"]

    if corrected_params.get("qualify") and corrected_params.get("limit"):
        raise ValueError("NUNCA use LIMIT com QUALIFY - use QUALIFY para múltiplas dimensões")

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
            # Adiciona ORDER BY ao final se não estiver presente
            order_by = _parse_list_param(corrected_params.get("order_by"), "order_by")
            # Verifica se já existe ORDER BY na query
            if order_by:
                order_by_clause = f" ORDER BY {', '.join(order_by)}"
                if "ORDER BY" not in query_clean.upper():
                    query_clean = query_clean.strip()
                    # Adiciona antes do último SELECT se houver mais de um, senão ao final
                    if query_clean.upper().count("SELECT") > 1:
                        # Adiciona ao final da última SELECT
                        last_select = query_clean.upper().rfind("SELECT")
                        # Busca o fim do último bloco SELECT
                        end_select = query_clean.rfind("GROUP BY")
                        if end_select != -1:
                            # Adiciona após GROUP BY
                            group_by_end = query_clean.find(" ", end_select)
                            if group_by_end == -1:
                                group_by_end = len(query_clean)
                            query_clean = query_clean[:group_by_end] + order_by_clause + query_clean[group_by_end:]
                        else:
                            query_clean += order_by_clause
                    else:
                        query_clean += order_by_clause
            print(f"DEBUG - Query construída:\n{query_clean}")
            return query_clean.strip()
        else:
            with_clause = f"WITH {cte_clean}\n"

    # 5. Caminho único: se não houver CTE, usa full_table_id como from_table automaticamente
    if cte:
        if not from_table or not str(from_table).strip():
            raise ValueError("O parâmetro 'from_table' é obrigatório e deve ser passado explicitamente pelo modelo quando houver CTE.")
    else:
        if not from_table or not str(from_table).strip():
            from_table = full_table_id
    if from_table == corrected_params.get("full_table_id") and not (from_table.startswith('`') and from_table.endswith('`')):
        from_table = f'`{from_table}`'

    # 6. Monta demais cláusulas
    where = f" WHERE {corrected_params['where']}" if corrected_params.get("where") else ""
    group_by_sql = f" GROUP BY {', '.join(filtered_group_by)}" if filtered_group_by else ""
    # Garante que todos os campos do eixo X e do parâmetro order_by estejam presentes
    # Se não houver order_by, adiciona automaticamente o campo temporal/dimensão principal
    if not order_by:
        # Prioriza campo temporal/dimensão principal
        temporal_fields = [f for f in select if re.search(r"data|mes|ano|dia|hora", f, re.IGNORECASE)]
        temporal_fields = [f.split(" AS ")[0].strip() for f in temporal_fields]
        for tf in temporal_fields:
            if tf not in order_by:
                order_by.append(tf)
        # Se ainda vazio, adiciona primeira dimensão do group_by
        if not order_by and filtered_group_by:
            order_by.append(filtered_group_by[0])
    order_by_sql = f" ORDER BY {', '.join(order_by)}" if order_by else ""
    qualify = f" QUALIFY {corrected_params['qualify']}" if corrected_params.get("qualify") else ""
    limit = f" LIMIT {int(corrected_params['limit'])}" if corrected_params.get("limit") else ""

    # 7. Monta query principal
    query = f"{with_clause}SELECT {', '.join(select)} FROM {from_table}{where}{group_by_sql}{qualify}{order_by_sql}{limit}"

    # 8. Remove espaços
    query_clean = re.sub(r'[\n\t]+', ' ', query)
    query_clean = re.sub(r' +', ' ', query_clean)

    # 9. Retorna sempre o SQL completo gerado
    print(f"DEBUG - Query construída:\n{query_clean}")
    return query_clean.strip()