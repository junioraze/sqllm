import os
from dotenv import load_dotenv
import add_instructions

load_dotenv(".env")

# Projeto e tabela
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
TABLE_ID = os.getenv("TABLE_ID")
MODEL_NAME = os.getenv("MODEL_NAME")
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Autenticação
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Instruções do sistema para o modelo Gemini
SYSTEM_INSTRUCTION = f"""
Você é um assistente de dados especializado em vendas de veículos.
SEMPRE use a função query_vehicle_sales para consultar dados da tabela {FULL_TABLE_ID}.
NUNCA mostre a consulta SQL diretamente ao usuário.
Após obter os dados brutos, faça todos os cálculos necessários e gere gráficos quando solicitado.

Regras estritas:
1. SEMPRE chame a função query_vehicle_sales para obter dados
2. NUNCA mostre SQL diretamente ao usuário
3. Para gráficos, analise os dados e inclua no final:
   GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna]

{add_instructions.COMPARACAO_INSTRUCOES}
{add_instructions.CAMPOS_DESCRICAO}
"""