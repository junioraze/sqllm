import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION
import re
import io
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px


def initialize_model():
    """
    Inicializa o modelo Gemini com a função query_vehicle_sales.
    """
    veiculos_vendas_func = FunctionDeclaration(
        name="query_vehicle_sales",
        description=(
            "Consulta vendas de veículos no BigQuery. "
            "Siga as regras de SQL do BigQuery Standard, nunca o Legacy, nunca utilize strftime para datas. "
            "GROUP BY e ORDER BY devem conter apenas nomes de colunas, sem funções de agregação. "
            "LIMIT deve ser inteiro. WHERE deve ser SQL puro."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "description": "Tipo de consulta (aggregation, comparison, raw_data)",
                    "enum": ["aggregation", "comparison", "raw_data"],
                },
                "select": {
                    "type": "array",
                    "description": "Campos a selecionar ou funções de agregação",
                    "items": {"type": "string"},
                },
                "where": {
                    "type": "string",
                    "description": "Condições WHERE em SQL puro",
                },
                "group_by": {
                    "type": "array",
                    "description": "Campos para agrupamento",
                    "items": {"type": "string"},
                },
                "order_by": {
                    "type": "array",
                    "description": "Campos para ordenação",
                    "items": {"type": "string"},
                },
                "limit": {"type": "integer", "description": "Limite de registros"},
            },
            "required": ["select"],
        },
    )
    veiculos_tool = Tool(function_declarations=[veiculos_vendas_func])
    return genai.GenerativeModel(
        MODEL_NAME, tools=[veiculos_tool], system_instruction=SYSTEM_INSTRUCTION
    )


def generate_chart(data, chart_type, x_axis, y_axis, title=""):
    """
    Gera um gráfico Plotly moderno e elegante para dashboards executivos.
    """
    if not data or not x_axis or not y_axis:
        return None
    df = pd.DataFrame(data)
    fig = None

    # Paleta executiva: azul, cinza, verde, laranja
    palette = ["#1565C0", "#43A047", "#F9A825", "#546E7A", "#00838F"]

    if chart_type == "bar":
        fig = px.bar(
            df, x=x_axis, y=y_axis,
            template="plotly_white",
            color_discrete_sequence=palette,
            title=title or f"{y_axis} por {x_axis}"
        )
        fig.update_traces(
            marker=dict(line=dict(width=1, color="#222")),
            hovertemplate=f"<b>%{{x}}</b><br>{y_axis}: <b>%{{y}}</b><extra></extra>",
        )
    elif chart_type == "line":
        fig = px.line(
            df, x=x_axis, y=y_axis, markers=True,
            template="plotly_white",
            color_discrete_sequence=palette,
            title=title or f"{y_axis} por {x_axis}"
        )
        fig.update_traces(
            marker=dict(size=9, line=dict(width=2, color="#222")),
            hovertemplate=f"<b>%{{x}}</b><br>{y_axis}: <b>%{{y}}</b><extra></extra>",
        )
    elif chart_type == "pie":
        fig = px.pie(
            df, names=x_axis, values=y_axis,
            template="plotly_white",
            color_discrete_sequence=palette,
            title=title or f"{y_axis} por {x_axis}"
        )
    else:
        return None

    fig.update_layout(
        font=dict(family="Segoe UI, Arial", size=16, color="#222"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        title_font=dict(size=20, family="Segoe UI, Arial", color="#1565C0"),
        xaxis_title=x_axis,
        yaxis_title=y_axis,
    )
    return fig

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
       - Gráfico se solicitado (usando formato GRAPH-TYPE)
       - Atenção à formatação para evitar erros de markdown.

    PERGUNTA DO USUÁRIO: "{prompt}"

    DADOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}

    FORMATO ESPERADO DA RESPOSTA:
    [Contexto e introdução]

    [Análise dos principais resultados]

    [Tabela ou resumo dos dados quando relevante]

    [Sugestão de gráfico se aplicável, no formato:]
    GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna]
    - O tipo pode ser "bar" ou "line", nunca gere "pie". As colunas devem existir nos dados fornecidos.
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
            y_axis = graph_part.split("Y-AXIS:")[1].strip()
            fig = generate_chart(data, graph_type, x_axis, y_axis)
            print("DEBUG generate_chart:", fig)
            if fig:
                chart_info = {"type": graph_type, "x": x_axis, "y": y_axis, "fig": fig}
                print("DEBUG chart_info criado:", chart_info)
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
                )
                response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        except Exception as e:
            print(f"Erro ao processar instrução de gráfico: {e}")

    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data,
        "chart_info": chart_info,
    }
    response_text = re.sub(r"GRAPH-TYPE:.*", "", response_text).strip()
    return response_text, tech_details
