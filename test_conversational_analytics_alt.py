"""
Teste de diagnóstico para Conversational Analytics API.
Verifica:
1. Se o project_id está correto
2. Se as APIs estão habilitadas
3. Se as permissões funcionam
4. Qual é o erro exato
"""

import os
import json
from google.cloud import geminidataanalytics
from google.api_core import gapic_v1
from google.auth import default
from dotenv import load_dotenv

# Carrega env
load_dotenv()

print("=" * 80)
print("TESTE DE DIAGNÓSTICO - Conversational Analytics API")
print("=" * 80)
print()

# ============ 1. Verificar Credenciais ============
print("[1] VERIFICANDO CREDENCIAIS")
print("-" * 80)

credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './gl.json')
print(f"Caminho de credenciais: {credentials_path}")

if os.path.exists(credentials_path):
    with open(credentials_path) as f:
        creds_data = json.load(f)
    print(f"✅ Arquivo encontrado")
    print(f"   Type: {creds_data.get('type')}")
    print(f"   Project: {creds_data.get('project_id')}")
    print(f"   Email: {creds_data.get('client_email')}")
else:
    print(f"❌ Arquivo não encontrado em {credentials_path}")

print()

# ============ 2. Verificar Project ID ============
print("[2] VERIFICANDO PROJECT ID")
print("-" * 80)

PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID')

print(f"PROJECT_ID: {PROJECT_ID}")
print(f"DATASET_ID: {DATASET_ID}")

if not PROJECT_ID:
    print("❌ PROJECT_ID não definido no .env")
else:
    print(f"✅ PROJECT_ID definido: {PROJECT_ID}")

print()

# ============ 3. Testar Autenticação ============
print("[3] TESTANDO AUTENTICAÇÃO")
print("-" * 80)

try:
    credentials, default_project = default()
    print(f"✅ Autenticação OK")
    print(f"   Projeto padrão: {default_project}")
except Exception as e:
    print(f"❌ Erro de autenticação: {e}")
    exit(1)

print()

# ============ 4. Testar Client Initialization ============
print("[4] INICIALIZANDO CLIENTS")
print("-" * 80)

try:
    # Force GOOGLE_CLOUD_PROJECT
    os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID or 'bigquery-for-ml'
    
    print(f"GOOGLE_CLOUD_PROJECT setado para: {os.environ['GOOGLE_CLOUD_PROJECT']}")
    print()
    
    print("Criando DataAgentServiceClient...")
    data_agent_client = geminidataanalytics.DataAgentServiceClient()
    print(f"✅ DataAgentServiceClient criado")
    
    print("Criando DataChatServiceClient...")
    data_chat_client = geminidataanalytics.DataChatServiceClient()
    print(f"✅ DataChatServiceClient criado")
    
except Exception as e:
    print(f"❌ Erro ao criar clients: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()

# ============ 5. Testar Acesso ao Agent ============
print("[5] TESTANDO ACESSO AO AGENT")
print("-" * 80)

AGENT_ID = os.getenv('AGENT_ID', 'agent_8f51992b-552c-4778-9790-b619f8196dc5')
LOCATION = 'global'

print(f"Agent ID: {AGENT_ID}")
print(f"Projeto: {PROJECT_ID}")
print(f"Localização: {LOCATION}")
print()

try:
    agent_path = data_agent_client.data_agent_path(PROJECT_ID, LOCATION, AGENT_ID)
    print(f"Agent path: {agent_path}")
    
    request = geminidataanalytics.GetDataAgentRequest(name=agent_path)
    print(f"Tentando obter agent...")
    agent = data_agent_client.get_data_agent(request=request)
    print(f"✅ Agent encontrado!")
    
except Exception as e:
    print(f"⚠️  Agent não existe (esperado se for primeiro acesso): {e}")
    print(f"   Tipo do erro: {type(e).__name__}")

print()

# ============ 6. Testar Criação de Conversa ============
print("[6] TESTANDO CRIAÇÃO DE CONVERSA")
print("-" * 80)

import uuid

conversation_id = f"test_{uuid.uuid4().hex[:8]}"
print(f"Conversation ID: {conversation_id}")
print()

try:
    # Primeiro, criar uma conversation com um agent
    print("Criando conversation com agent...")
    
    # Precisa passar o agent_path na conversation
    agent_path = data_agent_client.data_agent_path(PROJECT_ID, LOCATION, AGENT_ID)
    
    conversation = geminidataanalytics.Conversation(
        agents=[agent_path]  # ← AQUI: agents deve ter pelo menos um
    )
    
    request = geminidataanalytics.CreateConversationRequest(
        parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
        conversation_id=conversation_id,
        conversation=conversation,
    )
    
    print(f"Request criado: {type(request)}")
    print(f"Parent: {request.parent}")
    print(f"Conversation ID: {request.conversation_id}")
    print(f"Conversation agents: {request.conversation.agents}")
    print()
    
    print("ENVIANDO REQUEST...")
    response = data_chat_client.create_conversation(request=request)
    
    print(f"✅ CONVERSA CRIADA COM SUCESSO!")
    print(f"   Resposta: {response}")
    
except Exception as e:
    print(f"❌ ERRO ao criar conversa: {e}")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Código: {getattr(e, 'code', 'N/A')}")
    print()
    
    # Tentar extrair detalhes do erro
    error_details = str(e)
    if '403' in error_details:
        print("🔍 ANÁLISE DO ERRO 403:")
        print("   - Permissão negada para cloudaicompanion.conversations.create")
        print("   - Possíveis causas:")
        print("     1. Cloud AI Companion API não habilitada")
        print("     2. Service account sem rolle 'Cloud AI Companion Admin'")
        print("     3. Projeto não suporta Cloud AI Companion")
        print()
        print("   PRÓXIMOS PASSOS:")
        print("   1. Ir para Google Cloud Console → APIs & Services")
        print("   2. Procurar por 'Cloud AI Companion API'")
        print("   3. Verificar se está habilitada")
        print("   4. Se não estiver, enable-la")
        print("   5. Aguardar 2-3 minutos para propagação")
        print("   6. Tenta novamente")
    elif '400' in error_details and 'agents' in error_details:
        print("🔍 ANÁLISE DO ERRO 400 (Agents):")
        print("   - A conversation precisa ter agents ou context")
        print("   - Solução: Passar agent_path na Conversation")
        print("   - Formato: conversation.agents = [agent_path]")
    
    import traceback
    print()
    print("Full traceback:")
    traceback.print_exc()

print()
print("=" * 80)
print("FIM DO TESTE")
print("=" * 80)

