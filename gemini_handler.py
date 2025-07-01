import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION
import re
import json
import pandas as pd
import plotly.express as px
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes
from datetime import datetime

def initialize_model():
    """
    Inicializa o modelo Gemini com instruções mais rígidas para múltiplas dimensões
    """
    veiculos_vendas_func = FunctionDeclaration(
        name="query_vehicle_sales",
        description=(
            "Consulta vendas de veículos no BigQuery. REGRAS ABSOLUTAS:\n"
            "1. Para TOP N por grupo (ex: top 3 por estado) USE QUALIFY com PARTITION BY\n"
            "2. NUNCA use LIMIT para consultas agrupadas\n"
            "3. Para múltiplas dimensões inclua TODOS os campos do PARTITION BY no SELECT\n"
            "4. Campos no GROUP BY DEVEM estar no SELECT\n\n"
            "Exemplo CORRETO para top 3 modelos por estado:\n"
            "{\n"
            '  "select": ["modelo", "uf", "SUM(QTE) AS total"],\n'
            '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
            '  "group_by": ["modelo", "uf"],\n'
            '  "order_by": ["uf", "total DESC"],\n'
            '  "qualify": "ROW_NUMBER() OVER (PARTITION BY uf ORDER BY total DESC) <= 3"\n'
            "}"
        ),
        parameters={
            "type": "object",
            "properties": {
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
            "required": ["select"],
        },
    )

    veiculos_tool = Tool(function_declarations=[veiculos_vendas_func])

    # Configuração mais rígida do modelo
    generation_config = {
        "temperature": 0.5,  # Reduz criatividade para seguir regras
        "max_output_tokens": 2000,
    }

    return genai.GenerativeModel(
        MODEL_NAME,
        tools=[veiculos_tool],
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
