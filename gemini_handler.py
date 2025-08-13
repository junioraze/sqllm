import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION, TABLES_CONFIG, PROJECT_ID, DATASET_ID
import re
import json
import pandas as pd
import plotly.express as px
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes
from datetime import datetime

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
        "🔥 **REGRA ADICIONAL**: Para comparações, rankings com detalhamento, ou múltiplas métricas → SEMPRE CTE!"
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
        "temperature": 0.5,
        "max_output_tokens": 2000,
    }

    return genai.GenerativeModel(
        MODEL_NAME,
        tools=[business_tool],
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=generation_config,
    )


def generate_chart(data, chart_type, x_axis, y_axis, color=None):
    """Gera gráfico com tratamento para múltiplas dimensões"""
    if not data or not x_axis or not y_axis:
        return None

    try:
        df = pd.DataFrame.from_records(data)

        # Verificação de colunas com tratamento para múltiplas dimensões
        required_columns = {x_axis, y_axis}
        if color:  # Terceira dimensão
            required_columns.add(color)
            if color not in df.columns:
                color = None  # Degrada para 2D

        # Conversão segura de tipos para eixos
        df[y_axis] = pd.to_numeric(df[y_axis], errors="coerce")

        # Paleta de cores para múltiplas categorias
        palette = px.colors.qualitative.Plotly

        if chart_type == "bar":
            fig = px.bar(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                barmode="group",  # Essencial para múltiplas dimensões
                color_discrete_sequence=palette,
                title="Viz"  # Título personalizado em vez de "undefined"
            )
        elif chart_type == "line":
            fig = px.line(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                markers=True,
                color_discrete_sequence=palette,
                title="Viz"  # Título personalizado em vez de "undefined"
            )
        else:
            return None

        fig.update_layout(
            hovermode="x unified", 
            plot_bgcolor="rgba(255, 255, 255, 0.95)",  # Fundo branco
            paper_bgcolor="rgba(255, 255, 255, 0.95)",  # Papel branco
            font=dict(
                color="#093374",  # Azul mais escuro
                size=14,
                family="Arial, sans-serif"
            ),
            title=dict(
                text="",  # Remove o título completamente
                font=dict(
                    color="#093374",  # Azul mais escuro
                    size=18,
                    family="Arial, sans-serif"
                ),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                gridcolor="rgba(0, 0, 0, 0.1)",
                color="#093374",  # Azul mais escuro
                tickfont=dict(
                    color="#093374",  # Azul mais escuro
                    size=13,
                    family="Arial, sans-serif"
                ),
                title=dict(
                    font=dict(
                        color="#093374",  # Azul mais escuro
                        size=14,
                        family="Arial, sans-serif"
                    )
                )
            ),
            yaxis=dict(
                gridcolor="rgba(0, 0, 0, 0.1)",
                color="#093374",  # Azul mais escuro
                tickfont=dict(
                    color="#093374",  # Azul mais escuro
                    size=13,
                    family="Arial, sans-serif"
                ),
                title=dict(
                    font=dict(
                        color="#093374",  # Azul mais escuro
                        size=14,
                        family="Arial, sans-serif"
                    )
                )
            ),
            legend=dict(
                font=dict(
                    color="#093374",  # Azul mais escuro
                    size=12,
                    family="Arial, sans-serif"
                ),
                bgcolor="rgba(255, 255, 255, 0.9)",  # Fundo branco
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            hoverlabel=dict(
                bgcolor="rgba(255, 255, 255, 0.95)",  # Fundo branco
                font_color="#093374",  # Azul mais escuro
                bordercolor="rgba(0, 0, 0, 0.2)",
                font_size=12,
                font_family="Arial, sans-serif"
            ),
            autosize=True,  # Permite redimensionamento automático
            height=500,     # Altura mínima para evitar compressão
            margin=dict(l=60, r=60, t=60, b=60)
        )
        return fig

    except Exception as e:
        print(f"Erro ao gerar gráfico (multi-dimensão): {str(e)}")
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
    - O tipo pode ser "bar" ou "line", nunca gere "pie". 
    - COLOR é opcional e deve ser usado para representar a terceira dimensão.
    - As colunas devem existir nos dados fornecidos.

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

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(instruction)
    response_text = response.text
    chart_info = None

    # Extrai instrução de gráfico, se houver
    if "GRAPH-TYPE:" in response_text:
        try:
            graph_part = response_text.split("GRAPH-TYPE:")[1].strip()
            graph_type = graph_part.split("|")[0].strip()
            x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
            y_axis = graph_part.split("Y-AXIS:")[1].split("|")[0].strip()
            color = None
            if "COLOR:" in graph_part:
                color = graph_part.split("COLOR:")[1].strip()

            fig = generate_chart(data, graph_type, x_axis, y_axis, color)
            #print("DEBUG generate_chart:", fig)
            if fig:
                chart_info = {
                    "type": graph_type,
                    "x": x_axis,
                    "y": y_axis,
                    "color": color,
                    "fig": fig,
                }

            else:
                print(
                    "DEBUG gráfico não gerado. Dados:",
                    data,
                    "Tipo:",
                    graph_type,
                    "X:",
                    x_axis,
                    "Y:",
                    y_axis,
                    "Color:",
                    color,
                )
                response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        except Exception as e:
            print(f"Erro ao processar instrução de gráfico: {e}")

    # Verificar se o usuário solicitou exportação
    export_requested = any(keyword in prompt.lower() for keyword in 
                          ['exportar', 'excel', 'planilha', 'csv', 'baixar']) or "EXPORT:" in response_text
    
    # Gerar links de exportação se solicitado
    export_links = []
    export_info = {}
    
    if export_requested:
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
    
    context_prompt = f"""
🚨 VALIDADOR INTELIGENTE DE REUTILIZAÇÃO DE DADOS 🚨

MISSÃO: Analisar o histórico e determinar se alguma consulta anterior pode responder à nova pergunta.

NOVA PERGUNTA: "{current_prompt}"

{history_context}

🧠 ANÁLISE INTELIGENTE APRIMORADA:

🔴 REGRAS CRÍTICAS PARA CONSULTAS COMPLEXAS:

1. **ANÁLISE DE COMPATIBILIDADE DE DADOS**:
   - A nova pergunta precisa de colunas que NÃO EXISTEM nos dados anteriores? → NOVA CONSULTA
   - Ex: Histórico tem "modelo, total_vendas" mas nova pergunta pede "evolução mensal" → NOVA CONSULTA (falta coluna de data)
   - Ex: Histórico tem dados agregados (somas, totais) mas nova pergunta pede detalhamento temporal → NOVA CONSULTA

2. **CONSULTAS DE TOP N + EVOLUÇÃO TEMPORAL**:
   - Se a nova pergunta pede "evolução" ou "por mês/ano" de um ranking anterior → SEMPRE NOVA CONSULTA
   - Dados de ranking (ex: "top 5 modelos") são agregados e não têm detalhamento temporal
   - Ex: Histórico "top 20 modelos" + Nova pergunta "evolução mensal dos 5 melhores" → NOVA CONSULTA

3. **MUDANÇA DE GRANULARIDADE**:
   - Histórico tem dados totalizados mas nova pergunta pede breakdown (por período, região, etc.) → NOVA CONSULTA
   - Histórico tem dados detalhados mas nova pergunta pede apenas resumo → PODE REUTILIZAR

4. **COMPATIBILIDADE DE ASSUNTO**:
   - Nova pergunta é sobre o MESMO ASSUNTO da consulta anterior? 
   - Ex: Nova pergunta sobre "tempo médio" vs histórico sobre "montante de vendas" → INCOMPATÍVEL → NOVA CONSULTA

5. **QUANTIDADE E ESCOPO**:
   - Se a nova pergunta solicita mais registros do que qualquer consulta anterior retornou → NOVA CONSULTA
   - Se a nova pergunta muda filtros, período, ou critérios → NOVA CONSULTA

6. **TIPO DE ANÁLISE**:
   - Se a nova pergunta pede cálculos/análises diferentes dos já feitos → NOVA CONSULTA
   - Se a nova pergunta pede métricas não calculadas anteriormente → NOVA CONSULTA

7. **VISUALIZAÇÃO/EXPORT APENAS**:
   - Se a nova pergunta só quer apresentar os mesmos dados de forma diferente → PODE REUTILIZAR
   - Ex: "fazer gráfico", "exportar excel", "mostrar tabela" dos mesmos dados → REUTILIZAR

🎯 DECISÃO PRIORITÁRIA:
- **EVOLUÇÃO TEMPORAL + RANKING**: Se nova pergunta combina ranking com evolução temporal → SEMPRE NOVA CONSULTA
- **FALTA DE COLUNAS**: Se nova pergunta precisa de colunas não disponíveis nos dados anteriores → NOVA CONSULTA
- **GRANULARIDADE DIFERENTE**: Se nova pergunta precisa de mais detalhes que os dados agregados anteriores → NOVA CONSULTA
- **VISUALIZAÇÃO APENAS**: Se nova pergunta só quer gráfico/export dos mesmos dados → REUTILIZAR

Responda APENAS:
{{"should_reuse": false, "reason": "nova pergunta sobre evolução temporal requer dados com detalhamento que não existem no histórico agregado"}}
OU
{{"should_reuse": true, "reason": "consulta anterior contém dados suficientes", "interaction_id": "ID_da_consulta"}}
"""

    try:
        # Usa um modelo simples só para avaliação, sem tools
        evaluation_model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={"temperature": 0.1, "max_output_tokens": 200}  # Temperatura mais baixa para decisões mais consistentes
        )
        
        response = evaluation_model.generate_content(context_prompt)
        response_text = response.text.strip()
        
        # Tenta extrair JSON da resposta
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            return result
        else:
            return {"should_reuse": False, "reason": "Resposta inválida do modelo"}
            
    except Exception as e:
        print(f"Erro na avaliação de reutilização: {str(e)}")
        # Em caso de erro, não reutiliza por segurança
        return {"should_reuse": False, "reason": f"Erro na avaliação: {str(e)}"}
