# 🚀 Sistema de Análise de Dados com IA - Configuração para Clientes

Este sistema é completamente desacoplado e reutilizável para diferentes clientes. Siga as instruções abaixo para configurar para um novo cliente.

## 📋 Arquivos de Configuração

### 1. `client_config.json` - Configuração Visual e Textual
```json
{
  "app_title": "Nome do Sistema do Cliente",
  "app_subtitle": "Subtítulo para a tela de login", 
  "business_domain": "domínio de negócio (ex: vendas, financeiro)",
  "data_source": "descrição da fonte de dados",
  "rate_limit_description": "tipo de requisições",
  "examples": [
    "- Exemplo de pergunta 1",
    "- Exemplo de pergunta 2", 
    "- Exemplo de pergunta 3"
  ],
  "limitations": {
    "data_access": "Texto sobre acesso aos dados",
    "cross_reference": "Texto sobre limitações de cruzamento",
    "single_query": "Texto sobre consultas simultâneas",
    "temporal_comparisons": "Texto sobre comparações temporais",
    "model_understanding": "Texto sobre compreensão do modelo", 
    "data_freshness": "Texto sobre atualização dos dados"
  }
}
```

### 2. `tables_config.json` - Configuração das Tabelas
```json
{
  "nome_da_tabela": {
    "description": "Descrição da tabela para o Gemini",
    "instructions": "Instruções específicas da tabela",
    "examples": [
      "Exemplo de uso 1",
      "Exemplo de uso 2"
    ]
  }
}
```

### 3. `credentials.json` - Credenciais de Acesso
```json
{
  "login": "email@cliente.com",
  "password": "senha_cliente"
}
```

### 4. `.env` - Variáveis de Ambiente
```
PROJECT_ID=projeto-bigquery
DATASET_ID=dataset_cliente
DATASET_LOG_ID=logs_cliente
MODEL_NAME=gemini-1.5-pro
CLIENTE_NAME=NomeCliente
MAX_REQUEST_DAY=100
GOOGLE_APPLICATION_CREDENTIALS=caminho/para/service-account.json
```

## 🔧 Configuração para Novo Cliente

### Passo 1: Copie o Template
```bash
cp client_config_template.json client_config.json
```

### Passo 2: Personalize client_config.json
- Altere `app_title` para o nome do sistema do cliente
- Ajuste `business_domain` para o domínio específico (vendas, estoque, etc.)
- Modifique `examples` com perguntas relevantes aos dados do cliente
- Personalize todas as `limitations` conforme necessário

### Passo 3: Configure as Tabelas
- Edite `tables_config.json` com as tabelas específicas do cliente
- Adicione descrições detalhadas e instruções para cada tabela
- Inclua exemplos de uso relevantes

### Passo 4: Configure Credenciais e Ambiente
- Atualize `credentials.json` com login/senha do cliente
- Configure `.env` com projeto BigQuery e dataset do cliente
- Configure service account do Google Cloud

### Passo 5: Teste a Configuração
```bash
python main.py
```

## 📁 Estrutura de Arquivos para Cliente

```
sqllm/
├── main.py                     # Código principal (não modificar)
├── config.py                   # Carregamento de configs (não modificar)
├── client_config.json          # ✏️ PERSONALIZAR POR CLIENTE
├── tables_config.json          # ✏️ PERSONALIZAR POR CLIENTE  
├── credentials.json            # ✏️ PERSONALIZAR POR CLIENTE
├── .env                        # ✏️ PERSONALIZAR POR CLIENTE
├── gemini_handler.py           # Código IA (não modificar)
├── database.py                 # Código SQL (não modificar)
├── cache_db.py                 # Código cache (não modificar)
├── utils.py                    # Utilitários (não modificar)
├── style.py                    # Estilos (não modificar)
├── rate_limit.py               # Rate limit (não modificar)
└── logger.py                   # Logs (não modificar)
```

## ✅ Vantagens do Desacoplamento

1. **Reutilização Total**: O mesmo código serve para qualquer cliente
2. **Facilidade de Deploy**: Apenas troque os arquivos de configuração  
3. **Manutenção Simples**: Updates no core beneficiam todos os clientes
4. **Personalização Completa**: Cada cliente tem sua identidade visual/textual
5. **Versionamento Limpo**: Sem código específico de cliente no repositório

## 🎯 Exemplos de Configuração por Indústria

### E-commerce
```json
{
  "business_domain": "vendas online e produtos",
  "examples": [
    "- Quais produtos mais vendidos em 2024?",
    "- Compare vendas por categoria mensalmente",
    "- Demonstre o faturamento por região"
  ]
}
```

### Financeiro
```json
{
  "business_domain": "transações financeiras",
  "examples": [
    "- Qual o volume de transações por mês?",
    "- Compare receitas vs despesas em 2024",
    "- Demonstre o fluxo de caixa por categoria"
  ]
}
```

### RH
```json
{
  "business_domain": "recursos humanos e colaboradores", 
  "examples": [
    "- Quantos colaboradores por departamento?",
    "- Compare turnover entre 2023 e 2024",
    "- Demonstre a distribuição salarial por cargo"
  ]
}
```

## 🚀 Deploy Rápido

Para cada novo cliente, apenas:
1. Clone o repositório
2. Configure os 4 arquivos personalizáveis
3. Execute o sistema

**Tempo estimado de configuração: 15-30 minutos** ⚡
