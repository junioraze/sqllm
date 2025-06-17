from google.cloud import bigquery
from config import FULL_TABLE_ID

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
    """Constrói a query SQL com base nos parâmetros recebidos."""
    tipo_insight = params.get("tipo_insight")
    periodo = params.get("periodo")
    periodo_comparacao = params.get("periodo_comparacao")
    modelo_veiculo = params.get("modelo")
    uf = params.get("uf")
    revenda = params.get("revenda")
    agrupar_por = params.get("agrupar_por", [])
    nivel_agregacao = params.get("nivel_agregacao_temporal", "mes")

    where_clauses = []
    
    # Filtros básicos
    if uf:
        where_clauses.append(f"uf = '{uf}'")
    if modelo_veiculo:
        where_clauses.append(f"modelo = '{modelo_veiculo}'")
    if revenda:
        where_clauses.append(f"revenda = '{revenda}'")

    # Lógica para diferentes tipos de insights
    if tipo_insight == "comparacao":
        anos = []
        if periodo:
            anos.append(periodo)
        if periodo_comparacao:
            anos.append(periodo_comparacao)
        
        if anos:
            where_clauses.append(f"EXTRACT(YEAR FROM dta_venda) IN ({', '.join(anos)})")
        
        # MODIFICAÇÃO PRINCIPAL AQUI
        if nivel_agregacao == "ano":
            select_fields = [
                "EXTRACT(YEAR FROM dta_venda) as ano",
                "SUM(val_compra) as total_vendas",
                "COUNT(*) as quantidade"
            ]
            group_by_fields = ["ano"]
        else:  # mes
            select_fields = [
                "EXTRACT(YEAR FROM dta_venda) as ano",
                "EXTRACT(MONTH FROM dta_venda) as mes",
                "SUM(val_compra) as total_vendas",
                "COUNT(*) as quantidade"
            ]
            group_by_fields = ["ano", "mes"]
        
        query = f"""
            SELECT {', '.join(select_fields)}
            FROM `{FULL_TABLE_ID}`
            {f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""}
            GROUP BY {', '.join(group_by_fields)}
            ORDER BY {', '.join(group_by_fields)}
        """
    else:
        # Lógica para outros tipos de insights
        if periodo:
            if '-' in periodo:
                year, month = periodo.split('-')
                where_clauses.append(f"EXTRACT(YEAR FROM dta_venda) = {year}")
                where_clauses.append(f"EXTRACT(MONTH FROM dta_venda) = {month}")
            else:
                where_clauses.append(f"EXTRACT(YEAR FROM dta_venda) = {periodo}")

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        if tipo_insight == "total":
            query = f"SELECT SUM(val_compra) as total_vendas FROM `{FULL_TABLE_ID}` {where_sql}"
        elif tipo_insight == "por modelo":
            query = f"SELECT modelo, SUM(val_compra) as total_vendas, COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql} GROUP BY modelo ORDER BY modelo"
        elif tipo_insight == "por UF":
            query = f"SELECT uf, SUM(val_compra) as total_vendas, COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql} GROUP BY uf ORDER BY uf"
        elif tipo_insight == "por revenda":
            query = f"SELECT revenda, SUM(val_compra) as total_vendas, COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql} GROUP BY revenda ORDER BY revenda"
        elif tipo_insight == "quantidade":
            query = f"SELECT COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql}"
        elif tipo_insight == "por período":
            if nivel_agregacao == "ano":
                query = f"SELECT EXTRACT(YEAR FROM dta_venda) as ano, SUM(val_compra) as total_vendas, COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql} GROUP BY ano ORDER BY ano"
            else:
                query = f"SELECT FORMAT_DATE('%Y-%m', dta_venda) as mes, SUM(val_compra) as total_vendas, COUNT(*) as quantidade FROM `{FULL_TABLE_ID}` {where_sql} GROUP BY mes ORDER BY mes"
        elif tipo_insight == "multidimensional":
            select_fields = []
            group_by_fields = []
            
            if "ano" in agrupar_por or "mes" in agrupar_por:
                if nivel_agregacao == "ano":
                    select_fields.append("EXTRACT(YEAR FROM dta_venda) as ano")
                    group_by_fields.append("ano")
                else:
                    select_fields.append("FORMAT_DATE('%Y-%m', dta_venda) as mes")
                    group_by_fields.append("mes")
            
            if "uf" in agrupar_por:
                select_fields.append("uf")
                group_by_fields.append("uf")
            if "modelo" in agrupar_por:
                select_fields.append("modelo")
                group_by_fields.append("modelo")
            if "revenda" in agrupar_por:
                select_fields.append("revenda")
                group_by_fields.append("revenda")
            
            select_fields.extend([
                "SUM(val_compra) as total_vendas",
                "COUNT(*) as quantidade"
            ])
            
            query = f"""
                SELECT {', '.join(select_fields)}
                FROM `{FULL_TABLE_ID}`
                {where_sql}
                {f'GROUP BY {", ".join(group_by_fields)}' if group_by_fields else ''}
                ORDER BY {group_by_fields[0] if group_by_fields else '1'}
            """
        else:
            query = f"SELECT * FROM `{FULL_TABLE_ID}` {where_sql} LIMIT 10"
    
    return query