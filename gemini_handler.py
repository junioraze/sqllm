import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION, TABLES_CONFIG, PROJECT_ID, DATASET_ID
import re
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes
from subscription_system_db import SubscriptionSystem
from datetime import datetime
# Importações removidas - tema universal não requer funções específicas

def initialize_model():
    """
    Inicializa o modelo Gemini com instruções dinâmicas baseadas nas tabelas configuradas
    """
    
    # Constrói a descrição dinamicamente baseada nas tabelas disponíveis com full_table_id
    tables_description = "Consulta dados no BigQuery. Tabelas disponíveis:\n"
    full_table_mapping = {}
    
    for table_name, config in TABLES_CONFIG.items():
        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        full_table_mapping[full_table_id] = table_name
        tables_description += f"- {full_table_id}: {config['description']}\n"
    
    tables_description += (
        "\nREGRAS ABSOLUTAS:\n"
        "1. 🚨 CONSULTAS COMPLEXAS - REGRAS CRÍTICAS:\n"
        "   � **QUANDO USAR CTE (WITH) - REGRA DE OURO**:\n"
        "   - SEMPRE que o usuário pedir MAIS DE UMA COISA na pergunta → USE CTE!\n"
        "   - Ex: 'top 5 modelos MAIS vendidos E sua evolução mensal' = 2 coisas → CTE obrigatório\n"
        "   - Ex: 'produtos com melhor performance E detalhamento por região' = 2 coisas → CTE obrigatório\n"
        "   - Ex: 'ranking de vendedores E histórico de cada um' = 2 coisas → CTE obrigatório\n"
        "\n"
        "   🎯 **ESTRATÉGIA CTE PARA PERGUNTAS COMPOSTAS**:\n"
        "   - ETAPA 1 (CTE): Resolva a primeira parte (ex: identificar TOP N)\n"
        "   - ETAPA 2 (SELECT principal): Use o CTE para resolver a segunda parte (ex: evolução)\n"
        "   - MUITO mais simples que subqueries complexas!\n"
        "\n"
        "   🔴 Para 'TOP N + EVOLUÇÃO TEMPORAL' (ex: 'top 5 modelos mais vendidos e evolução mensal'):\n"
        "   - CTE: Identifica TOP N no período COMPLETO (sem PARTITION BY mes)\n"
        "   - SELECT: Usa CTE no WHERE com IN() para filtrar evolução temporal\n"
        "   - NUNCA use PARTITION BY mes quando o objetivo é TOP N geral + evolução\n"
        "\n"
        "   ✅ **EXEMPLO PRÁTICO - ESTRATÉGIA SIMPLES COM CTE**:\n"
        "   Pergunta: 'top 5 modelos mais vendidos de 2025 e evolução mensal'\n"
        "   \n"
        "   Estratégia CTE (RECOMENDADA):\n"
        "   {\n"
        f'     "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '     "with_cte": "top_5_modelos AS (SELECT modelo FROM tabela WHERE EXTRACT(YEAR FROM data) = 2025 GROUP BY modelo QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(vendas) DESC) <= 5)",\n'
        '     "select": ["modelo", "FORMAT_DATE(\'%Y-%m\', data) AS periodo_mes", "SUM(vendas) AS vendas_mes"],\n'
        '     "where": "EXTRACT(YEAR FROM data) = 2025 AND modelo IN (SELECT modelo FROM top_5_modelos)",\n'
        '     "group_by": ["modelo", "FORMAT_DATE(\'%Y-%m\', data)"],\n'
        '     "order_by": ["modelo", "periodo_mes"]\n'
        "   }\n"
        "\n"
        "   ❌ **EVITE**: Subqueries complexas no WHERE quando CTE é mais claro!\n"
        "\n"
        "2. 🚨 QUALIFY - REGRAS:\n"
        "   - Para TOP N GERAL: NUNCA use PARTITION BY, use apenas ORDER BY\n"
        "   - Para TOP N POR GRUPO: use PARTITION BY com o campo do grupo\n"
        "   - PARTITION BY só funciona com campos que estão no GROUP BY\n"
        "3. NUNCA use LIMIT para consultas agrupadas - sempre use QUALIFY\n"
        "4. Para múltiplas dimensões inclua TODOS os campos do PARTITION BY no SELECT\n"
        "5. Campos no GROUP BY DEVEM estar no SELECT\n"
        "6. SEMPRE use a tabela correta baseada na pergunta do usuário\n"
        "7. 🔴 GRÁFICOS TEMPORAIS - REGRA CRÍTICA:\n"
        "   Para análises temporais (vendas por mês/ano, evolução temporal), SEMPRE crie uma coluna de data contínua:\n"
        "   - NUNCA use EXTRACT(MONTH FROM data) - quebra continuidade temporal\n"
        "   - USE: CONCAT(EXTRACT(YEAR FROM data), '-', LPAD(EXTRACT(MONTH FROM data), 2, '0')) AS periodo_mes\n"
        "   - OU: FORMAT_DATE('%Y-%m', data) AS periodo_mes\n"
        "   - OU: FORMAT_DATE('%Y-%m-%d', data) AS periodo_dia (para dados diários)\n"
        "   - OU: EXTRACT(YEAR FROM data) AS ano (apenas para dados anuais)\n"
        "   Isso garante visualização correta em gráficos de linha temporal!\n\n"
        "Exemplo CORRETO para top 20 modelos (SEM PARTITION BY):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["modelo", "SUM(QTE) AS total_vendas"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["modelo"],\n'
        '  "order_by": ["total_vendas DESC"],\n'
        '  "qualify": "ROW_NUMBER() OVER (ORDER BY total_vendas DESC) <= 20"\n'
        "}\n\n"
        "Exemplo CORRETO para top 3 modelos por estado (COM PARTITION BY):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["modelo", "uf", "SUM(QTE) AS total"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["modelo", "uf"],\n'
        '  "order_by": ["uf", "total DESC"],\n'
        '  "qualify": "ROW_NUMBER() OVER (PARTITION BY uf ORDER BY total DESC) <= 3"\n'
        "}\n\n"
        "Exemplo CORRETO para vendas mensais (gráfico temporal):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["FORMAT_DATE(\'%Y-%m\', dta_venda) AS periodo_mes", "SUM(QTE) AS total_vendas"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["FORMAT_DATE(\'%Y-%m\', dta_venda)"],\n'
        '  "order_by": ["periodo_mes"]\n'
        "}\n\n"
        "🔥 **CTE (Common Table Expressions) PARA CONSULTAS COMPLEXAS**:\n"
        "🎯 **QUANDO USAR**: Toda pergunta com 'E' ou múltiplas intenções!\n\n"
        "📚 **CATÁLOGO DE EXEMPLOS CTE PARA NEGÓCIOS**:\n\n"
        "✅ **EXEMPLO 1: TOP N + EVOLUÇÃO TEMPORAL**\n"
        "Pergunta: 'top 5 modelos mais vendidos de 2025 e evolução mensal'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "top_modelos AS (SELECT modelo FROM tabela WHERE EXTRACT(YEAR FROM data) = 2025 GROUP BY modelo QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(vendas) DESC) <= 5)",\n'
        '  "select": ["modelo", "FORMAT_DATE(\'%Y-%m\', data) AS periodo_mes", "SUM(vendas) AS vendas_mes"],\n'
        '  "where": "EXTRACT(YEAR FROM data) = 2025 AND modelo IN (SELECT modelo FROM top_modelos)",\n'
        '  "group_by": ["modelo", "FORMAT_DATE(\'%Y-%m\', data)"],\n'
        '  "order_by": ["modelo", "periodo_mes"]\n'
        "}\n\n"
        "✅ **EXEMPLO 2: COMPARAÇÃO ENTRE PERÍODOS**\n"
        "Pergunta: 'vendas atuais vs mesmo período ano anterior dos melhores produtos'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "vendas_atual AS (SELECT produto, SUM(vendas) as vendas_2025 FROM tabela WHERE EXTRACT(YEAR FROM data) = 2025 GROUP BY produto), vendas_anterior AS (SELECT produto, SUM(vendas) as vendas_2024 FROM tabela WHERE EXTRACT(YEAR FROM data) = 2024 GROUP BY produto)",\n'
        '  "select": ["a.produto", "a.vendas_2025", "COALESCE(b.vendas_2024, 0) as vendas_2024", "ROUND((a.vendas_2025 - COALESCE(b.vendas_2024, 0)) / COALESCE(b.vendas_2024, 1) * 100, 2) as crescimento_percent"],\n'
        '  "from_table": "vendas_atual a LEFT JOIN vendas_anterior b ON a.produto = b.produto",\n'
        '  "where": "a.vendas_2025 > 0",\n'
        '  "order_by": ["crescimento_percent DESC"]\n'
        "}\n\n"
        "✅ **EXEMPLO 3: ANÁLISE DE PERFORMANCE + DETALHAMENTO**\n"
        "Pergunta: 'vendedores com melhor performance e detalhamento por região'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "top_vendedores AS (SELECT vendedor FROM tabela WHERE EXTRACT(YEAR FROM data) = 2025 GROUP BY vendedor QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(vendas) DESC) <= 10)",\n'
        '  "select": ["v.vendedor", "t.regiao", "SUM(v.vendas) AS vendas_regiao", "COUNT(*) AS total_transacoes"],\n'
        '  "from_table": "tabela v INNER JOIN top_vendedores t ON v.vendedor = t.vendedor",\n'
        '  "where": "EXTRACT(YEAR FROM v.data) = 2025",\n'
        '  "group_by": ["v.vendedor", "t.regiao"],\n'
        '  "order_by": ["vendas_regiao DESC"]\n'
        "}\n\n"
        "✅ **EXEMPLO 4: ANÁLISE DE CONCENTRAÇÃO + PARTICIPAÇÃO**\n"
        "Pergunta: 'principais clientes e participação nas vendas por categoria'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "top_clientes AS (SELECT cliente FROM tabela GROUP BY cliente QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(vendas) DESC) <= 20), total_categoria AS (SELECT categoria, SUM(vendas) as total FROM tabela GROUP BY categoria)",\n'
        '  "select": ["c.cliente", "v.categoria", "SUM(v.vendas) AS vendas_cliente", "ROUND(SUM(v.vendas) / tc.total * 100, 2) AS participacao_percent"],\n'
        '  "from_table": "top_clientes c INNER JOIN tabela v ON c.cliente = v.cliente INNER JOIN total_categoria tc ON v.categoria = tc.categoria",\n'
        '  "group_by": ["c.cliente", "v.categoria", "tc.total"],\n'
        '  "order_by": ["participacao_percent DESC"]\n'
        "}\n\n"
        "✅ **EXEMPLO 5: ANÁLISE DE TENDÊNCIA + SAZONALIDADE**\n"
        "Pergunta: 'produtos com crescimento e padrão sazonal por trimestre'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "produtos_crescimento AS (SELECT produto FROM tabela WHERE data >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH) GROUP BY produto HAVING SUM(vendas) > (SELECT AVG(vendas_produto) FROM (SELECT produto, SUM(vendas) as vendas_produto FROM tabela GROUP BY produto)))",\n'
        '  "select": ["p.produto", "CONCAT(\'Q\', EXTRACT(QUARTER FROM v.data), \'-\', EXTRACT(YEAR FROM v.data)) AS trimestre", "SUM(v.vendas) AS vendas_trimestre"],\n'
        '  "from_table": "produtos_crescimento p INNER JOIN tabela v ON p.produto = v.produto",\n'
        '  "where": "v.data >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)",\n'
        '  "group_by": ["p.produto", "EXTRACT(QUARTER FROM v.data)", "EXTRACT(YEAR FROM v.data)"],\n'
        '  "order_by": ["p.produto", "trimestre"]\n'
        "}\n\n"
        "✅ **EXEMPLO 6: SEGMENTAÇÃO + ANÁLISE COMPORTAMENTAL**\n"
        "Pergunta: 'clientes premium e comportamento de compras por canal'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "clientes_premium AS (SELECT cliente FROM tabela GROUP BY cliente HAVING SUM(valor_compra) > 50000 AND COUNT(DISTINCT data) > 10)",\n'
        '  "select": ["cp.cliente", "v.canal_venda", "COUNT(*) AS total_compras", "AVG(v.valor_compra) AS ticket_medio", "SUM(v.valor_compra) AS valor_total"],\n'
        '  "from_table": "clientes_premium cp INNER JOIN tabela v ON cp.cliente = v.cliente",\n'
        '  "group_by": ["cp.cliente", "v.canal_venda"],\n'
        '  "order_by": ["valor_total DESC"]\n'
        "}\n\n"
        "✅ **EXEMPLO 7: ANÁLISE DE MARGEM + RENTABILIDADE**\n"
        "Pergunta: 'produtos mais rentáveis e análise de margem por região'\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.tabela",\n'
        '  "with_cte": "produtos_rentaveis AS (SELECT produto FROM tabela GROUP BY produto HAVING AVG((preco_venda - custo) / preco_venda) > 0.3 QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(preco_venda - custo) DESC) <= 15)",\n'
        '  "select": ["pr.produto", "v.regiao", "AVG((v.preco_venda - v.custo) / v.preco_venda * 100) AS margem_percent", "SUM(v.preco_venda - v.custo) AS lucro_total"],\n'
        '  "from_table": "produtos_rentaveis pr INNER JOIN tabela v ON pr.produto = v.produto",\n'
        '  "group_by": ["pr.produto", "v.regiao"],\n'
        '  "order_by": ["margem_percent DESC"]\n'
        "}\n\n"
        "🎯 **PADRÕES DE RECONHECIMENTO PARA CTE**:\n"
        "- **'E sua evolução'** → CTE com ranking + temporal\n"
        "- **'E detalhamento por'** → CTE com filtro + breakdown\n"
        "- **'vs período anterior'** → CTE múltiplos períodos\n"
        "- **'e participação em'** → CTE com totais + percentuais\n"
        "- **'com melhor X e análise Y'** → CTE filtro + análise detalhada\n"
        "- **'principais X e comportamento'** → CTE ranking + padrões\n\n"
        "✅ **VANTAGENS DO CTE PARA PERGUNTAS COMPOSTAS**:\n"
        "- 🎯 Separa claramente cada intenção da pergunta\n"
        "- 🚀 Muito mais simples que subqueries aninhadas\n"
        "- 🔧 Facilita manutenção e debugging\n"
        "- 💡 Permite reutilização de resultados intermediários\n"
        "- ✨ Query final mais legível e performática\n"
        "- 📊 Ideal para análises de negócio complexas\n"
        "\n"
        "🔥 **REGRA DE OURO**: Se a pergunta tem 'E' conectando duas análises → USE CTE!\n"
        "🔥 **REGRA ADICIONAL**: Para comparações, rankings com detalhamento, ou múltiplas métricas → SEMPRE CTE!\n\n"
        "🎨 **FORMATAÇÃO DE DADOS PARA GRÁFICOS - REGRA CRÍTICA**:\n"
        "⚠️ **PROBLEMA COMUM**: Dados em formato 'wide' (vendas_2024, vendas_2025) NÃO funcionam para gráficos de múltiplas linhas!\n\n"
        "✅ **SOLUÇÃO**: Para gráficos com múltiplas séries (ex: comparar anos), SEMPRE use formato 'long':\n"
        "- ❌ ERRADO: mes | vendas_2024 | vendas_2025\n"
        "- ✅ CORRETO: mes | ano | vendas\n\n"
        "🔧 **QUANDO REFORMATAR DADOS**:\n"
        "- Se usuário pedir 'gráfico', 'chart', 'visualização' após consulta comparativa\n"
        "- Se dados anteriores estão em formato wide (múltiplas colunas de valores)\n"
        "- Se precisar de múltiplas linhas/séries no gráfico\n\n"
        "📊 **REGRAS DE FORMATAÇÃO POR TIPO DE COMPARAÇÃO**:\n\n"
        "🔹 **COMPARAÇÃO DE ANOS (múltiplas linhas por ano)**:\n"
        "   - Eixo X: Apenas MÊS (01, 02, 03...)\n"
        "   - Color: ano (2024, 2025)\n"
        "   - SELECT: LPAD(EXTRACT(MONTH FROM data), 2, '0') AS mes, EXTRACT(YEAR FROM data) AS ano\n\n"
        "🔹 **COMPARAÇÃO DE MESES (múltiplas linhas por mês)**:\n"
        "   - Eixo X: Apenas ANO (2024, 2025)\n"
        "   - Color: mes\n"
        "   - SELECT: EXTRACT(YEAR FROM data) AS ano, LPAD(EXTRACT(MONTH FROM data), 2, '0') AS mes\n\n"
        "🔹 **SÉRIE TEMPORAL (evolução no tempo)**:\n"
        "   - Eixo X: Período completo (2024-01, 2024-02...)\n"
        "   - SELECT: FORMAT_DATE('%Y-%m', data) AS periodo\n\n"
        "✅ **EXEMPLO PRÁTICO - REFORMATAÇÃO PARA GRÁFICO**:\n"
        "Situação: Dados anteriores em formato wide, usuário pede gráfico\n"
        "Solução: Nova query em formato long:\n"
        "{\n"
        f'  \"full_table_id\": \"{PROJECT_ID}.{DATASET_ID}.tabela\",\n'
        '  \"select\": [\"LPAD(EXTRACT(MONTH FROM data), 2, \'0\') AS mes\", \"EXTRACT(YEAR FROM data) AS ano\", \"SUM(vendas) AS vendas\"],\n'
        '  \"where\": \"EXTRACT(YEAR FROM data) IN (2024, 2025)\",\n'
        '  \"group_by\": [\"EXTRACT(MONTH FROM data)\", \"EXTRACT(YEAR FROM data)\"],\n'
        '  \"order_by\": [\"EXTRACT(MONTH FROM data)\", \"ano\"]\n'
        "}\n\n"
        "🎯 **RESULTADO IDEAL PARA GRÁFICO COMPARATIVO**:\n"
        "mes | ano | vendas\n"
        "01  | 2024 | 145165895\n"
        "01  | 2025 | 178128981\n"
        "02  | 2024 | 186732356\n"
        "02  | 2025 | 195843210\n\n"
        "🚨 **ATENÇÃO - FORMATO DE MÊS PARA COMPARAÇÕES**:\n"
        "- Para comparar ANOS no mesmo gráfico: use apenas MÊS no eixo X\n"
        "- Para comparar MESES no mesmo gráfico: use apenas ANO no eixo X\n"
        "- NUNCA use formato 'YYYY-MM' quando comparar anos diferentes!\n"
        "- Use LPAD(EXTRACT(MONTH FROM data), 2, '0') para mês com zero à esquerda\n\n"
        "🚨 **DETECÇÃO AUTOMÁTICA**: Se dados anteriores têm padrão 'valor_ano1', 'valor_ano2' → SEMPRE reformate!\n\n"
        "⚡ **EXEMPLOS ESPECÍFICOS DE REFORMATAÇÃO**:\n\n"
        "❌ **ERRO COMUM - Formato temporal para comparação**:\n"
        "Query que gera: periodo_mes='2024-01', ano=2024, vendas=1000\n"
        "Problema: Eixo X terá '2024-01', '2024-02' vs '2025-01', '2025-02' (séries separadas)\n\n"
        "✅ **CORRETO - Formato de comparação**:\n"
        "Query que gera: mes='01', ano=2024, vendas=1000\n"
        "Resultado: Eixo X terá '01', '02', '03'... com linhas para 2024 e 2025 no mesmo ponto\n\n"
    )
    
    query_func = FunctionDeclaration(
        name="query_business_data",
        description=tables_description,
        parameters={
            "type": "object",
            "properties": {
                "full_table_id": {
                    "type": "string",
                    "description": f"ID completo da tabela no BigQuery (PROJECT.DATASET.TABLE). Opções: {', '.join(full_table_mapping.keys())}",
                    "enum": list(full_table_mapping.keys())
                },
                "with_cte": {
                    "type": "string",
                    "description": "CTE (Common Table Expression) para consultas complexas. Ex: 'top_modelos AS (SELECT modelo FROM tabela GROUP BY modelo QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(vendas) DESC) <= 5)'. Use para decomposição de consultas TOP N + evolução temporal."
                },
                "from_table": {
                    "type": "string", 
                    "description": "Tabela ou JOIN a usar no FROM. Se não especificado, usa a tabela física. Para CTE: 'nome_cte' ou 'cte1 c1 JOIN tabela t ON c1.campo = t.campo'"
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para SELECT (DEVE incluir todos do PARTITION BY)",
                },
                "where": {
                    "type": "string",
                    "description": "Condições WHERE (SQL puro)",
                },
                "group_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para GROUP BY (DEVEM estar no SELECT)",
                },
                "order_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para ORDER BY",
                },
                "qualify": {
                    "type": "string",
                    "description": "Para TOP N: ROW_NUMBER() OVER (ORDER BY...) <= N (SEM partition) OU ROW_NUMBER() OVER (PARTITION BY campo_grupo ORDER BY...) <= N (COM partition apenas para grupos diferentes)",
                },
                "limit": {
                    "type": "integer",
                    "description": "USO PROIBIDO para consultas agrupadas - apenas para consultas simples",
                },
            },
            "required": ["full_table_id", "select"],
        },
    )

    business_tool = Tool(function_declarations=[query_func])

    generation_config = {
        "temperature": 0.2,  # Ajustado para melhor seguimento de instruções
        "max_output_tokens": 2000,
    }

    return genai.GenerativeModel(
        MODEL_NAME,
        tools=[business_tool],
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=generation_config,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    )


def generate_chart(data, chart_type, x_axis, y_axis, color=None):
    """
    Cria gráficos com tema universal elegante que funciona em ambos os temas (escuro/claro)
    """
    if not data or not x_axis or not y_axis:
        print("❌ Dados insuficientes para gráfico")
        return None

    try:
        df = pd.DataFrame.from_records(data)
        print(f"📊 Criando gráfico {chart_type}: X={x_axis}, Y={y_axis}, Color={color}")

        # Validação de colunas
        if x_axis not in df.columns:
            print(f"❌ Coluna X '{x_axis}' não encontrada")
            return None
        
        if y_axis not in df.columns:
            print(f"❌ Coluna Y '{y_axis}' não encontrada")
            return None
            
        # Tratamento da coluna de cor
        if color and color not in df.columns:
            print(f"⚠️ Coluna COLOR '{color}' não encontrada, removendo")
            color = None

        # Conversão Y para numérico
        try:
            df[y_axis] = pd.to_numeric(df[y_axis], errors="coerce")
        except Exception as e:
            print(f"⚠️ Erro ao converter Y: {e}")

        # PALETA UNIVERSAL ELEGANTE - Funciona em ambos os temas
        UNIVERSAL_COLORS = [
            "#2563eb",  # Azul vibrante
            "#dc2626",  # Vermelho forte  
            "#059669",  # Verde esmeralda
            "#d97706",  # Laranja queimado
            "#7c3aed",  # Roxo vibrante
            "#0891b2",  # Azul turquesa
            "#ea580c",  # Laranja vibrante
            "#65a30d",  # Verde lima
            "#be185d",  # Rosa forte
            "#4338ca"   # Índigo
        ]

        # Criação do gráfico
        if chart_type == "bar":
            fig = px.bar(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                barmode="group" if color else "relative",
                color_discrete_sequence=UNIVERSAL_COLORS,
                title=""
            )
        elif chart_type == "line":
            fig = px.line(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                markers=True,
                color_discrete_sequence=UNIVERSAL_COLORS,
                title=""
            )
        else:
            print(f"❌ Tipo '{chart_type}' não suportado")
            return None

        # DETECTA O TEMA ATUAL PARA CORES ADAPTÁVEIS
        current_theme = st.session_state.get('theme_mode', 'escuro')
        
        if current_theme == 'escuro':
            # Cores para tema escuro - alta visibilidade
            font_color = "#e5e7eb"
            title_color = "#f9fafb"
            grid_color = "rgba(156, 163, 175, 0.4)"
            line_color = "#9ca3af"
            legend_bg = "rgba(31, 41, 55, 0.9)"
            legend_border = "rgba(156, 163, 175, 0.8)"
            hover_bg = "rgba(31, 41, 55, 0.95)"
            hover_text = "#f9fafb"
        else:
            # Cores para tema claro - alta legibilidade
            font_color = "#374151"
            title_color = "#1f2937"
            grid_color = "rgba(156, 163, 175, 0.3)"
            line_color = "#d1d5db"
            legend_bg = "rgba(255, 255, 255, 0.9)"
            legend_border = "rgba(209, 213, 219, 0.8)"
            hover_bg = "rgba(255, 255, 255, 0.95)"
            hover_text = "#1f2937"

        # LAYOUT ADAPTÁVEL AO TEMA
        fig.update_layout(
            # Fundo transparente - adapta-se ao tema do container
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            
            # Tipografia adaptável
            font=dict(
                family="Inter, 'Segoe UI', system-ui, sans-serif",
                size=13,
                color=font_color
            ),
            
            # Margem otimizada
            margin=dict(l=60, r=60, t=40, b=60),
            height=400,
            
            # Eixos adaptativos
            xaxis=dict(
                title=dict(
                    text=x_axis.replace('_', ' ').title(),
                    font=dict(size=14, color=title_color)
                ),
                tickfont=dict(size=12, color=font_color),
                gridcolor=grid_color,
                gridwidth=1,
                showgrid=True,
                zeroline=False,
                linecolor=line_color,
                linewidth=1
            ),
            
            yaxis=dict(
                title=dict(
                    text=y_axis.replace('_', ' ').title(),
                    font=dict(size=14, color=title_color)
                ),
                tickfont=dict(size=12, color=font_color),
                gridcolor=grid_color,
                gridwidth=1,
                showgrid=True,
                zeroline=True,
                zerolinecolor=grid_color,
                zerolinewidth=1,
                linecolor=line_color,
                linewidth=1
            ),
            
            # Legenda adaptável
            legend=dict(
                bgcolor=legend_bg,
                bordercolor=legend_border,
                borderwidth=1,
                font=dict(size=12, color=font_color),
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            
            showlegend=bool(color),
            
            # Hover adaptável
            hoverlabel=dict(
                bgcolor=hover_bg,
                bordercolor=legend_border,
                font=dict(size=12, color=hover_text)
            )
        )

        # Customização específica por tipo
        if chart_type == "bar":
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>",
                marker=dict(
                    line=dict(width=0.5, color="rgba(255,255,255,0.8)"),
                    opacity=0.9
                )
            )
        elif chart_type == "line":
            fig.update_traces(
                line=dict(width=3),
                marker=dict(size=8, line=dict(width=2, color="white")),
                hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>"
            )

        print("✅ Gráfico universal criado")
        return fig

    except Exception as e:
        print(f"❌ Erro ao criar gráfico: {str(e)}")
        return None


def generate_content_with_retry(model, prompt, max_retries=3):
    """
    Gera conteúdo com retry automático quando há bloqueio por segurança
    """
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            
            # Verifica se a resposta foi bloqueada
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    print(f"⚠️ Tentativa {attempt + 1}: Resposta bloqueada por segurança")
                    
                    if attempt < max_retries - 1:
                        # Reformula o prompt para ser menos propenso a bloqueio
                        if isinstance(prompt, str):
                            # Adiciona contexto técnico específico para dados empresariais
                            reformulated_prompt = f"""
                            CONTEXTO: Sistema de business intelligence para analise de dados corporativos.
                            AMBIENTE: Base de dados empresarial com informacoes de vendas, produtos e operacoes.
                            OBJETIVO: Processar consulta de dados para dashboard de gestao empresarial.
                            
                            SOLICITACAO DE ANALISE:
                            {prompt}
                            
                            FORMATO DE RESPOSTA: JSON estruturado para sistema de relatorios.
                            """
                            prompt = reformulated_prompt
                        
                        continue
                    else:
                        print("❌ Máximo de tentativas excedido - resposta bloqueada por segurança")
                        return None
                
                # Se chegou aqui, a resposta é válida
                return response
            else:
                print(f"⚠️ Tentativa {attempt + 1}: Nenhum candidato retornado")
                if attempt == max_retries - 1:
                    return None
                    
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}: Erro na geração - {str(e)}")
            if attempt == max_retries - 1:
                raise e
    
    return None


def refine_with_gemini(
    prompt: str, data: list, function_params: dict = None, query: str = None
):
    """
    Envia os dados para o Gemini fazer o refinamento e retorna a resposta e detalhes técnicos.
    """
    if function_params is not None:
        if hasattr(function_params, "_values"):
            function_params = {k: v for k, v in function_params.items()}
        elif not isinstance(function_params, dict):
            function_params = dict(function_params)

    instruction = f"""
    Você é um analista de dados especializado. Sua tarefa é:
    1. Analisar os dados fornecidos (em JSON abaixo) + a pergunta do usuário e gerar uma resposta completa e contextualizada.
    2. Responder à pergunta do usuário de forma completa.
    3. Formatar a resposta com:
       - Introdução contextual
       - Principais insights
       - Dados em formato tabular (quando aplicável)
       - Só gere gráficos se e somente se for solicitado a gerar (usando formato GRAPH-TYPE)
       - Só gere arquivos excel/xlsx ou csv se o usuário solicitar explicitamente (usando palavras como exportar, baixar, excel, planilha, csv).
       - Atenção à formatação para evitar erros de markdown.

    🔴 IMPORTANTE: Os dados fornecidos foram FILTRADOS e PROCESSADOS pelo BigQuery conforme a consulta SQL executada.
    Se a consulta SQL contém filtros (WHERE), os dados JÁ ESTÃO filtrados por esses critérios.
    
    CONSULTA SQL EXECUTADA: {query if query else "Consulta não disponível"}
    FILTROS APLICADOS: {function_params.get('where', 'Nenhum filtro') if function_params else 'Não disponível'}

    Os dados fornecidos são FINAIS e COMPLETOS para a pergunta feita. NÃO diga que faltam informações 
    se a consulta SQL já aplicou os filtros necessários.

    PERGUNTA DO USUÁRIO: "{prompt}"

    DADOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}

    FORMATO ESPERADO DA RESPOSTA:
    [Contexto e introdução]

    [Análise dos principais resultados]

    [Tabela ou resumo dos dados quando relevante]

    [Sugestão de gráfico se aplicável, no formato:]
    GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna] | COLOR: [coluna]
    
    🎯 **REGRAS INTELIGENTES PARA GRÁFICOS COMPARATIVOS**:
    
    **1. DETECÇÃO AUTOMÁTICA DE COMPARAÇÕES TEMPORAIS:**
    - Se os dados contêm períodos (anos, meses, trimestres) E múltiplas categorias → USE COLOR para a categoria principal
    - Exemplo: Vendas 2023 vs 2024 por modelo → COLOR: modelo (cada modelo = linha/barra diferente)
    - Exemplo: Evolução mensal por região → COLOR: regiao (cada região = linha diferente)
    
    **2. DETECÇÃO AUTOMÁTICA DE COMPARAÇÕES CATEGÓRICAS:**
    - Se pergunta menciona "comparar", "versus", "vs", "entre" → USE COLOR para dimensão de comparação
    - Se dados têm múltiplas categorias distintas → USE COLOR para categoria principal
    - Exemplo: "Vendas por produto vs região" → COLOR: produto OU regiao (escolha a mais relevante)
    
    **3. PADRÕES DE RECONHECIMENTO AUTOMÁTICO:**
    - **Temporal + Categoria**: "vendas mensais por modelo" → X: mês, Y: vendas, COLOR: modelo
    - **Múltiplos Anos**: "2023 vs 2024" → X: período, Y: valor, COLOR: ano
    - **Múltiplas Regiões**: "vendas por estado" → X: estado, Y: vendas, COLOR: (opcional se só uma métrica)
    - **Ranking Temporal**: "top 5 modelos evolução" → X: período, Y: vendas, COLOR: modelo
    
    **4. TIPO DE GRÁFICO INTELIGENTE:**
    - **TEMPORAL** (meses, anos, dias): SEMPRE "line" (para mostrar evolução)
    - **CATEGÓRICO** (produtos, regiões, ranking): SEMPRE "bar" (para comparar valores)
    - **EVOLUTIVO** (crescimento, tendência): SEMPRE "line"
    
    **5. ANÁLISE DOS DADOS FORNECIDOS:**
    Colunas disponíveis: {list(data[0].keys()) if data and len(data) > 0 else "Nenhuma"}
    
    **Detecção Automática para esta consulta:**
    - Se contém coluna temporal (ano, mês, período, data) → linha temporal
    - Se contém múltiplas categorias → use a categoria principal como COLOR
    - Se dados agregados por período + categoria → linha com COLOR por categoria
    
    **DIRETRIZES COLOR AUTOMÁTICO:**
    - ✅ Use COLOR quando há MÚLTIPLAS séries para comparar
    - ✅ Use COLOR para dimensão que diferencia as linhas/barras
    - ❌ NÃO use COLOR se há apenas uma série de dados
    - ❌ NÃO use COLOR para eixo X ou Y

    [Exportação de dados se solicitado, no formato:]
    EXPORT-INFO: FORMATO: [excel/csv] 
    - Aqui você só precisa fornecer essa linha de EXPORT-INFO, não fornecer nenhuma informação a mais sobre o arquivo.
    
    ATENÇÃO: 
    Só gere visualização gráfica se o usuário solicitar explicitamente um gráfico, visualização, plot, curva, barra, linha ou termos semelhantes.
   - Nunca gere gráfico por padrão, nem sugira gráfico se não for solicitado.
        Exemplo: 
        Usuário: "Quais as vendas das lojas de limoeiro em janeiro/2025?"
        Resposta: [NÃO incluir gráfico]
        Usuário: "Me mostre um gráfico das vendas das lojas de limoeiro em janeiro/2025"
        Resposta: [Incluir gráfico conforme instrução]
        
    Se o usuário solicitar exportação, gere links para download dos dados em Excel e CSV. 
    - Nunca gere se não houver dados ou se não for explicitamente solicitado.
    """

    model = genai.GenerativeModel(
        MODEL_NAME,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    )
    
    # Usa a função de retry para contornar bloqueios de segurança
    response = generate_content_with_retry(model, instruction)
    
    if response is None:
        # Fallback se ainda assim não conseguir resposta
        return "⚠️ Não foi possível processar a solicitação. Tente reformular sua pergunta de forma mais específica.", None, None
    
    response_text = response.text
    chart_info = None

    # Extrai instrução de gráfico, se houver
    if "GRAPH-TYPE:" in response_text:
        try:
            graph_part = response_text.split("GRAPH-TYPE:")[1].strip()
            
            # Parse mais robusto dos parâmetros
            graph_type = graph_part.split("|")[0].strip().lower()
            
            # Extração segura do X-AXIS
            if "X-AXIS:" in graph_part:
                x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
            else:
                print("❌ X-AXIS não encontrado na instrução do gráfico")
                chart_info = None
                
            # Extração segura do Y-AXIS  
            if "Y-AXIS:" in graph_part:
                y_axis = graph_part.split("Y-AXIS:")[1].split("|")[0].strip()
            else:
                print("❌ Y-AXIS não encontrado na instrução do gráfico")
                chart_info = None
                
            # Extração segura do COLOR (opcional)
            color = None
            if "COLOR:" in graph_part:
                color_raw = graph_part.split("COLOR:")[1].strip()
                # Remove quebras de linha e espaços extras
                color = color_raw.split('\n')[0].split('\r')[0].strip()
                
                # Se color está vazio ou é "None", remove
                if not color or color.lower() == "none" or color == "":
                    color = None
                else:
                    print(f"🎨 COLOR detectado: '{color}'")

            print(f"📊 Parâmetros do gráfico - Tipo: {graph_type}, X: {x_axis}, Y: {y_axis}, Color: {color}")
            
            fig = generate_chart(data, graph_type, x_axis, y_axis, color)
            
            if fig:
                chart_info = {
                    "type": graph_type,
                    "x": x_axis,
                    "y": y_axis,
                    "color": color,
                    "fig": fig,
                }
                print("✅ Gráfico gerado com sucesso")
            else:
                print(f"❌ Falha ao gerar gráfico. Tipo: {graph_type}, X: {x_axis}, Y: {y_axis}, Color: {color}")
                chart_info = None
                
        except Exception as e:
            print(f"❌ Erro ao processar instrução de gráfico: {e}")
            chart_info = None

    # Verificar se o usuário solicitou exportação
    export_requested = any(keyword in prompt.lower() for keyword in 
                          ['exportar', 'excel', 'planilha', 'csv', 'baixar']) or "EXPORT:" in response_text
    
    # Gerar links de exportação se solicitado
    export_links = []
    export_info = {}
    
    if export_requested:
        # Verifica permissão para exportação
        has_permission, permission_message = SubscriptionSystem.check_feature_permission('excel_export')
        
        if not has_permission:
            # Substitui os links de exportação por mensagem de upgrade
            export_links.append(f"""
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px; margin: 8px 0;">
                <div style="color: #92400e; font-weight: 500;">📊 Exportação Restrita</div>
                <div style="color: #78350f; font-size: 14px; margin: 4px 0;">{permission_message}</div>
                <a href="#" onclick="document.querySelector('[data-testid=\\"nav_payment\\"]').click(); return false;" 
                   style="color: #f59e0b; font-weight: 500; text-decoration: none;">
                   📈 Fazer Upgrade →
                </a>
            </div>
            """)
            export_info['restriction'] = "upgrade_required"
        else:
            # Gerar Excel
            excel_bytes = generate_excel_bytes(data)
            if excel_bytes:
                excel_filename = f"dados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                excel_link = create_styled_download_button(excel_bytes, excel_filename, "Excel")
                export_links.append(excel_link)
                export_info['excel'] = excel_filename
            
            # Gerar CSV
            csv_bytes = generate_csv_bytes(data)
            if csv_bytes:
                csv_filename = f"dados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                csv_link = create_styled_download_button(csv_bytes, csv_filename, "CSV")
                export_links.append(csv_link)
                export_info['csv'] = csv_filename
            export_info['csv'] = csv_filename

    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data,
        "chart_info": {
            "type": chart_info["type"],
            "x": chart_info["x"],
            "y": chart_info["y"],
            "color": chart_info["color"],
            # "fig" removido para evitar erro de serialização no cache
        } if chart_info else None,
        "export_links": export_links,
        "export_info": export_info,
    }
    
    # Adicionar figura de volta ao chart_info para retorno (uso imediato)
    if chart_info:
        tech_details["chart_info"]["fig"] = chart_info["fig"]
    
    #response_text = re.sub(r"GRAPH-TYPE:.*", "", response_text).strip()
    return response_text, tech_details


def should_reuse_data(model, current_prompt: str, user_history: list = None) -> dict:
    """
    Pergunta ao Gemini se deve reutilizar os dados das últimas consultas
    considerando o histórico do usuário e validação de estrutura de dados
    Retorna um dict com 'should_reuse': bool e 'reason': str
    """
    if not user_history:
        return {"should_reuse": False, "reason": "Nenhum histórico disponível"}
    
    # Constrói contexto do histórico recente com detalhes das colunas
    history_items = []
    for interaction in user_history:
        data_summary = f" ({interaction.get('raw_data_count', 0)} registros)" if interaction.get('raw_data_count', 0) > 0 else ""
        interaction_id = interaction.get('id', 'N/A')
        
        # Adiciona informações sobre a estrutura dos dados (colunas disponíveis)
        columns_info = ""
        if interaction.get('first_ten_table_lines'):
            try:
                first_record = json.loads(interaction.get('first_ten_table_lines', '[]'))
                if first_record and isinstance(first_record, list) and len(first_record) > 0:
                    columns = list(first_record[0].keys())
                    columns_info = f" | Colunas: {', '.join(columns)}"
            except:
                pass
        
        history_items.append(f"- ID: {interaction_id} | {interaction.get('user_prompt', 'N/A')}{data_summary}{columns_info}")
    
    if not history_items:
        return {"should_reuse": False, "reason": "Histórico vazio"}
        
    history_context = f"\nHISTÓRICO RECENTE (com IDs e estrutura de dados para referência):\n" + "\n".join(history_items) + "\n"
    
    # PROMPT ORIGINAL PRESERVADO - apenas linguagem técnica para evitar filtros
    context_prompt = f"""
ANÁLISE TÉCNICA DE COMPATIBILIDADE DE DADOS

CONSULTA ATUAL: "{current_prompt}"

{history_context}

CRITÉRIOS DE AVALIAÇÃO:

1. COMPATIBILIDADE DE DADOS:
   - A nova consulta requer colunas que NÃO EXISTEM nos dados anteriores → NOVA CONSULTA
   - Dados históricos agregados vs consulta que solicita detalhamento → NOVA CONSULTA

2. ANÁLISE DE GRANULARIDADE:
   - Consulta solicita evolução temporal de ranking anterior → NOVA CONSULTA
   - Dados totalizados vs solicitação de breakdown detalhado → NOVA CONSULTA

3. COMPATIBILIDADE DE ESCOPO:
   - Nova consulta aborda o MESMO ASSUNTO da consulta anterior? 
   - Mudança de filtros, período ou critérios → NOVA CONSULTA

4. FORMATO DE DADOS PARA GRÁFICOS (CRÍTICO):
   - Se consulta atual menciona 'gráfico', 'chart', 'visualização' E dados anteriores têm formato 'wide' (ex: vendas_2024, vendas_2025) → NOVA CONSULTA
   - Gráficos de múltiplas linhas precisam formato 'long' (ano | valor) não 'wide' (valor_2024 | valor_2025) → NOVA CONSULTA
   - Se dados anteriores têm padrão 'campo_ano1', 'campo_ano2' E consulta pede gráfico → NOVA CONSULTA
   - Se dados têm formato temporal 'YYYY-MM' E consulta pede comparação de anos → NOVA CONSULTA
   - Para gráficos comparativos: precisa eixo X simples (só mês) + color (ano) → NOVA CONSULTA se formato atual é temporal

5. REUTILIZAÇÃO VÁLIDA:
   - Consulta anterior contém dados suficientes para responder → REUTILIZAR
   - Apenas mudança de visualização dos mesmos dados → REUTILIZAR
   - Dados já estão no formato correto para o tipo de análise solicitada → REUTILIZAR

Responda APENAS em formato JSON:
{{"should_reuse": false, "reason": "descrição técnica"}}
OU
{{"should_reuse": true, "reason": "dados compatíveis", "interaction_id": "ID"}}
"""

    try:
        # Usa função de retry com configurações anti-bloqueio
        response = generate_content_with_retry(model, context_prompt)
        
        if response is None:
            print("⚠️ Modelo indisponível - usando fallback (nova consulta)")
            return {"should_reuse": False, "reason": "Fallback: nova consulta por indisponibilidade"}
        
        # Verificação robusta da resposta
        if not response.candidates or len(response.candidates) == 0:
            print("⚠️ Sem candidatos - usando fallback")
            return {"should_reuse": False, "reason": "Fallback: nova consulta por segurança"}
        
        candidate = response.candidates[0]
        
        # Verifica finish_reason
        if hasattr(candidate, 'finish_reason'):
            if candidate.finish_reason == 2:  # SAFETY
                print("⚠️ Bloqueio de segurança - usando fallback")
                return {"should_reuse": False, "reason": "Fallback: nova consulta (filtro de segurança)"}
            elif candidate.finish_reason != 1:  # STOP
                print(f"⚠️ Finish reason inesperado: {candidate.finish_reason} - usando fallback")
                return {"should_reuse": False, "reason": f"Fallback: finish_reason {candidate.finish_reason}"}
        
        # Extrai texto da resposta
        response_text = ""
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
        
        if not response_text.strip():
            print("⚠️ Resposta vazia - usando fallback")
            return {"should_reuse": False, "reason": "Fallback: resposta vazia"}
        
        response_text = response_text.strip()
        
        # Parse do JSON da resposta
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            if "should_reuse" in result and "reason" in result:
                print(f"✅ Análise do modelo: {result}")
                return result
            else:
                print("⚠️ JSON incompleto - usando fallback")
                return {"should_reuse": False, "reason": "Fallback: estrutura JSON inválida"}
        else:
            print(f"⚠️ Resposta sem JSON: {response_text[:100]}... - usando fallback")
            return {"should_reuse": False, "reason": "Fallback: formato de resposta inválido"}
            
    except Exception as e:
        print(f"⚠️ Erro na análise: {str(e)} - usando fallback")
        return {"should_reuse": False, "reason": f"Fallback: erro na análise ({str(e)[:50]})"}

