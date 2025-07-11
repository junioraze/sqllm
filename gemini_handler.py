import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION, TABLES_CONFIG
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
    
    # Constrói a descrição dinamicamente baseada nas tabelas disponíveis
    tables_description = "Consulta dados no BigQuery. Tabelas disponíveis:\n"
    for table_name, config in TABLES_CONFIG.items():
        tables_description += f"- {table_name}: {config['description']}\n"
    
    tables_description += (
        "\nREGRAS ABSOLUTAS:\n"
        "1. Para TOP N por grupo (ex: top 3 por estado) USE QUALIFY com PARTITION BY\n"
        "2. NUNCA use LIMIT para consultas agrupadas\n"
        "3. Para múltiplas dimensões inclua TODOS os campos do PARTITION BY no SELECT\n"
        "4. Campos no GROUP BY DEVEM estar no SELECT\n"
        "5. SEMPRE use a tabela correta baseada na pergunta do usuário\n\n"
        "Exemplo CORRETO para top 3 modelos por estado:\n"
        "{\n"
        '  "table_name": "drvy_VeiculosVendas",\n'
        '  "select": ["modelo", "uf", "SUM(QTE) AS total"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["modelo", "uf"],\n'
        '  "order_by": ["uf", "total DESC"],\n'
        '  "qualify": "ROW_NUMBER() OVER (PARTITION BY uf ORDER BY total DESC) <= 3"\n'
        "}"
    )
    
    query_func = FunctionDeclaration(
        name="query_business_data",
        description=tables_description,
        parameters={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": f"Nome da tabela no BigQuery. Opções: {', '.join(TABLES_CONFIG.keys())}",
                    "enum": list(TABLES_CONFIG.keys())
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
                    "description": "CONDIÇÃO OBRIGATÓRIA para TOP N: ROW_NUMBER() OVER (PARTITION BY...) <= N",
                },
                "limit": {
                    "type": "integer",
                    "description": "USO PROIBIDO para consultas agrupadas - apenas para consultas simples",
                },
            },
            "required": ["table_name", "select"],
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
            )
        elif chart_type == "line":
            fig = px.line(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                markers=True,
                color_discrete_sequence=palette,
            )
        else:
            return None

        fig.update_layout(hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)")
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

    IMPORTANTE: Os dados fornecidos são FINAIS e COMPLETOS. NÃO tente solicitar dados adicionais, 
    fazer comparações com períodos não presentes nos dados, ou sugerir que faltam informações 
    se a pergunta pode ser respondida com os dados disponíveis.

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
        "chart_info": chart_info,
        "export_links": export_links,
        "export_info": export_info,
    }
    #response_text = re.sub(r"GRAPH-TYPE:.*", "", response_text).strip()
    return response_text, tech_details


def should_reuse_data(model, current_prompt: str, last_data: dict, user_history: list = None) -> dict:
    """
    Pergunta ao Gemini se deve reutilizar os dados da última consulta
    considerando o histórico do usuário
    Retorna um dict com 'should_reuse': bool e 'reason': str
    """
    if not last_data.get("raw_data") or not last_data.get("prompt"):
        return {"should_reuse": False, "reason": "Nenhum dado anterior disponível"}
    
    # Constrói contexto do histórico recente (últimas 5 interações)
    history_context = ""
    if user_history:
        recent_history = user_history[-5:]  # Últimas 5 interações
        history_items = []
        for interaction in recent_history:
            history_items.append(f"- {interaction.get('user_prompt', 'N/A')}")
        if history_items:
            history_context = f"\nHISTÓRICO RECENTE:\n" + "\n".join(history_items) + "\n"
    
    context_prompt = f"""
Analise se a nova pergunta pode ser respondida REUTILIZANDO os dados da consulta anterior:
{history_context}
PERGUNTA ANTERIOR: "{last_data.get('prompt', '')}"
NOVA PERGUNTA: "{current_prompt}"

DADOS DISPONÍVEIS: {len(last_data.get('raw_data', []))} registros da última consulta

🔴 REGRA FUNDAMENTAL: SEJA EXTREMAMENTE CONSERVADOR na reutilização!

✅ REUTILIZAR APENAS nos casos ÓBVIOS de exportação/visualização:
- "gerar excel", "exportar csv", "baixar planilha" dos MESMOS dados EXATOS
- "criar gráfico", "fazer visualização" dos MESMOS dados EXATOS
- "mostrar em tabela", "formatar em HTML" dos MESMOS dados EXATOS
- Reformulação simples da mesma resposta (sem mudança de dados)

❌ NUNCA REUTILIZAR quando houver QUALQUER tipo de:
- CONTAGEM: "conte", "contar", "quantos", "contagem" → SQL COUNT()
- AGREGAÇÃO: "some", "total", "média", "máximo", "mínimo" → SQL SUM(), AVG(), MAX(), MIN()
- AGRUPAMENTO: "por modelo", "por categoria", "por ano" → SQL GROUP BY
- ORDENAÇÃO diferente: "mais vendidos", "ranking" → SQL ORDER BY
- CÁLCULOS: "porcentagem", "percentual", "proporção" → SQL com cálculos
- FILTROS adicionais: "apenas Honda", "só 2024" → SQL WHERE
- COMPARAÇÕES: "compare", "versus", "diferença" → SQL JOINS/UNION
- PERÍODOS diferentes: qualquer ano/mês/data diferente
- LOCAIS diferentes: qualquer estado/cidade/região diferente
- PRODUTOS/MODELOS diferentes ou específicos
- Palavras como: "também", "além disso", "inclua", "mostre mais"
- Qualquer palavra que indica TRANSFORMAÇÃO dos dados

🚨 CASOS CRÍTICOS QUE SEMPRE REQUEREM NOVA CONSULTA:
- "conte os modelos" → SQL: SELECT modelo, COUNT(*) ... GROUP BY modelo
- "quantos por estado" → SQL: SELECT estado, COUNT(*) ... GROUP BY estado  
- "total de vendas" → SQL: SELECT SUM(quantidade) ...
- "modelos mais vendidos" → SQL: ... ORDER BY vendas DESC
- "apenas Honda" → SQL: ... WHERE marca = 'Honda'
- "dados de 2024" → SQL: ... WHERE ano = 2024

LEMBRE-SE: O BigQuery é MUITO mais eficiente para agregações/contagens/filtros 
do que tentar fazer isso localmente com os dados já retornados!

EXEMPLOS PRÁTICOS:
✅ "gere um excel desses dados" → REUTILIZAR (exportação)
❌ "conte os modelos" → NOVA CONSULTA (COUNT + GROUP BY)
❌ "quantos Honda?" → NOVA CONSULTA (COUNT + WHERE)
❌ "mais vendidos primeiro" → NOVA CONSULTA (ORDER BY)
❌ "total geral" → NOVA CONSULTA (SUM)

Responda APENAS no formato JSON válido:
{{"should_reuse": true, "reason": "explicação clara"}}
ou
{{"should_reuse": false, "reason": "explicação clara"}}
"""

    try:
        # Usa um modelo simples só para avaliação, sem tools
        evaluation_model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={"temperature": 0.0, "max_output_tokens": 200}  # Mais tokens para processar instruções complexas
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
