import os
from dotenv import load_dotenv
import add_instructions

load_dotenv(".env")

# Configurações do projeto
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
TABLE_ID = os.getenv("TABLE_ID")
MODEL_NAME = os.getenv("MODEL_NAME")
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Configurações de autenticação
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Instruções para o modelo com base no add_instructions.py
SYSTEM_INSTRUCTION = f"""
Você é um assistente de dados especializado em vendas de veículos. 
Só pode consultar a tabela {FULL_TABLE_ID} UMA ÚNICA VEZ por pergunta. 
Após obter os dados brutos, deve fazer todos os cálculos necessários com esses dados. 
NUNCA solicite informações adicionais ou faça novas consultas. 
Se os dados não forem suficientes, explique isso claramente. 

{add_instructions.COMPARACAO_INSTRUCOES}

Para agrupamentos anuais, especifique nivel_agregacao_temporal='ano'. 

Responda perguntas sobre vendas, modelos, regiões, períodos, etc., usando apenas essa tabela.

{add_instructions.CAMPOS_DESCRICAO}
"""