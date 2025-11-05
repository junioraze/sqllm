# 🤖 GL SQL LM - Sistema de Análise de Dados com IA

Sistema inteligente de análise de dados que utiliza Large Language Models (Gemini) e Retrieval-Augmented Generation (RAG) para converter perguntas em linguagem natural em queries SQL complexas, executadas automaticamente no Google BigQuery.

---

## 📋 Estrutura do Projeto

```
gl_sqllm/
├── config/                      # 🔧 Configurações e schemas
│   ├── settings.py             # Carregamento de configs (multi-path lookup)
│   ├── google_auth.py          # Autenticação Google Cloud (NOVO)
│   ├── tables_config.json      # Metadados das tabelas (USER-SPECIFIC)
│   ├── client_config.json      # Configuração de cliente (USER-SPECIFIC)
│   ├── credentials.json        # Credenciais autenticação (USER-SPECIFIC)
│   ├── payment_config.json     # Configuração de pagamentos (USER-SPECIFIC)
│   ├── rate_limit_state.json   # Estado dos limites (USER-SPECIFIC)
│   ├── sql_patterns.json       # Padrões SQL reutilizáveis
│   └── __init__.py
│
├── database/                    # 💾 Camada de persistência
│   ├── query_builder.py        # Construção e validação de queries
│   ├── query_cache.py          # Cache de queries executadas
│   ├── validator.py            # Validação de SQL com Gemini
│   ├── sql_validator_v2.py     # Validador SQL v2
│   └── __init__.py
│
├── llm_handlers/                # 🤖 Integração com modelos de IA
│   ├── gemini_handler.py       # Interface com Gemini API
│   ├── prompt_rules.py         # Regras de prompts e templates
│   └── __init__.py
│
├── rag_system/                  # 🧠 Sistema de Retrieval-Augmented Generation
│   ├── manager.py              # Gerenciador singleton de RAG (NOVO)
│   ├── business_metadata_rag_v3.py    # RAG v3: Multi-factor scoring
│   ├── business_metadata_rag.py       # RAG v2: Fallback
│   ├── sql_pattern_rag.py             # RAG para padrões SQL
│   ├── sql_pattern_rag_v2.py          # RAG v2 para padrões
│   └── __init__.py
│
├── ui/                          # 🎨 Interface com Streamlit
│   ├── main.py                 # App principal
│   ├── deepseek_theme.py       # Temas e estilização
│   ├── config_menu.py          # Menu de configuração
│   └── __init__.py
│
├── utils/                       # 🛠️ Utilitários gerais
│   ├── cache.py                # Cache de interações (DuckDB)
│   ├── logger.py               # Logging estruturado
│   ├── metrics.py              # Coleta de métricas
│   ├── rate_limit.py           # Sistema de rate limiting
│   ├── auth_system.py          # Autenticação de usuários
│   ├── image_utils.py          # Utilidades de imagens
│   ├── helpers.py              # Funções auxiliares
│   └── __init__.py
│
├── generators/                  # 🔨 Ferramentas de geração
│   ├── table_config_generator.py   # Gerador automático de schemas
│   ├── cli.py                      # Interface CLI
│   ├── __main__.py                 # Entry point
│   └── __init__.py
│
├── tests/                       # 🧪 Testes
│   ├── test_backend_flow.py    # Testes end-to-end do backend
│   └── __init__.py
│
├── docs/                        # 📖 Documentação
│   ├── logtable.sql            # Schema de log no BigQuery
│   └── __init__.py
│
├── etc/                         # 🎨 Recursos estáticos
│   ├── planos.py               # Configuração de planos
│   └── __init__.py
│
├── .streamlit/                  # ⚙️ Configuração do Streamlit
│   └── config.toml
│
├── requirements.txt            # Dependências Python
├── .gitignore                  # Arquivos ignorados pelo Git
├── .env                        # Variáveis de ambiente (USER-SPECIFIC)
├── gl_sqllm.service            # Serviço systemd
└── README.md                   # Este arquivo
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python 3.11+**
- **Git**
- **Google Cloud Project** com BigQuery habilitado
- **Gemini API Key**
- **Linux/macOS** (ou WSL no Windows)

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/junioraze/sqllm.git
cd gl_sqllm
```

### Passo 2: Criar Ambiente Virtual

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Credenciais (⚠️ IMPORTANTE)

Você precisa criar os seguintes arquivos em `config/`:

#### 1. **gl.json** - Credenciais Google Cloud
Baixe do Google Cloud Console:
- Vá para: Cloud Console → Service Accounts
- Crie uma conta de serviço com permissões para BigQuery
- Baixe o JSON e salve em `config/gl.json`

```json
{
  "type": "service_account",
  "project_id": "seu-projeto-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

#### 2. **credentials.json** - Autenticação de Usuários
```json
{
  "login": "seu_usuario@email.com",
  "password": "sua_senha_criptografada"
}
```

#### 3. **client_config.json** - Configuração do Cliente

Define o título, domínio de negócio, limites e exemplos do sistema. **Campos suportados:**

```json
{
  "app_title": "Sistema de Análise de Dados",
  "app_subtitle": "Assistente de IA para análise de dados",
  "business_domain": "dados",
  "data_source": "tabelas configuradas",
  "rate_limit_description": "requisições",
  "examples": [
    "- Qual foi o volume de vendas no último mês?",
    "- Me mostre a distribuição por região",
    "- Quais são os produtos mais vendidos?"
  ],
  "limitations": {
    "data_access": "Este assistente só pode consultar as tabelas configuradas no sistema.",
    "cross_reference": "Não é possível acessar ou cruzar dados de outras tabelas ou fontes externas.",
    "single_query": "Apenas uma consulta por vez é permitida.",
    "temporal_comparisons": "Para comparações temporais, utilize perguntas claras.",
    "model_understanding": "O modelo pode não compreender perguntas muito vagas.",
    "data_freshness": "Resultados são baseados nos dados mais recentes disponíveis."
  },
  "error_message": "Não foi possível processar sua solicitação no momento. Nossa equipe técnica foi notificada e está analisando a situação. Tente reformular sua pergunta ou entre em contato conosco."
}
```

**Uso nos arquivos:**
- `app_title`: Exibido no título da página (Streamlit)
- `app_subtitle`: Subtítulo da aplicação
- `business_domain`: Contexto do negócio (e.g., "vendas", "RH", "financeiro")
- `examples`: Exemplos de perguntas mostrados na tela inicial
- `limitations`: Restrições do sistema (exibidas no help)
- `error_message`: Mensagem padrão para erros (nunca mostrar stack trace ao usuário)

#### 4. **payment_config.json** - Configuração de Pagamentos (Opcional)
```json
{
  "enabled": false,
  "stripe_key": "sua_chave_stripe"
}
```

#### 5. **.env** - Variáveis de Ambiente
```env
ENVIRONMENT=prod
GEMINI_API_KEY=sua_chave_gemini_aqui
PROJECT_ID=seu-projeto-gcp
DATASET_ID=seu_dataset
```

### Passo 5: Configurar tables_config.json

Este arquivo define os metadados das suas tabelas. Exemplo:

```json
{
  "drvy_VeiculosVendas": {
    "metadata": {
      "table_id": "drvy_VeiculosVendas",
      "bigquery_table": "project.dataset.drvy_VeiculosVendas",
      "description": "Tabela de vendas de veículos",
      "domain": "vendas",
      "keywords": ["venda", "veículo", "carro", "moto"]
    },
    "fields": {
      "temporal_fields": [{"name": "data_venda", "type": "DATE"}],
      "dimension_fields": [{"name": "tipo_veiculo", "type": "STRING"}],
      "metric_fields": [{"name": "valor_venda", "type": "FLOAT64"}]
    },
    "business_rules": {
      "critical_rules": ["Sempre filtrar por ano >= 2023"]
    }
  }
}
```

---

## 🔐 Segurança e .gitignore

### Arquivos que NÃO devem ser versionados (USER-SPECIFIC)

Os seguintes arquivos contêm informações sensíveis e **NUNCA** devem ser commitados:

```
gl.json                    # Google Cloud credentials (CRÍTICO)
client_config.json        # Client configuration
credentials.json          # User credentials
payment_config.json       # Payment configuration
rate_limit_state.json     # Runtime state
cache.meta.json          # Cache metadata
sql_patterns_cache.*     # Cache files
ai_metrics.db            # Metrics database
users_new.db*            # User database
.env                     # Environment variables
.streamlit/secrets.toml  # Streamlit secrets
```

Todos esses arquivos já estão em `.gitignore`. Se você adicionar algum arquivo novo de configuração, adicione também ao `.gitignore`:

```bash
echo "meu_novo_arquivo.json" >> .gitignore
git add .gitignore
git commit -m "Add new config file to gitignore"
```

---

## 🎯 Como Usar

### Modo Desenvolvimento

```bash
# Com auto-reload de RAG ao editar tables_config.json
export ENVIRONMENT=dev
streamlit run ui/main.py
```

### Modo Produção

```bash
# Otimizado para performance
export ENVIRONMENT=prod
streamlit run ui/main.py --server.port 8052 --server.address 0.0.0.0
```

### Executar Testes

```bash
# Teste end-to-end do backend
python tests/test_backend_flow.py

# Teste específico
python tests/test_backend_flow.py --test-id 1
```

### Como Serviço Systemd

```bash
# Copiar arquivo de serviço
sudo cp gl_sqllm.service /etc/systemd/system/

# Ativar serviço
sudo systemctl enable gl_sqllm.service
sudo systemctl start gl_sqllm.service

# Verificar status
sudo systemctl status gl_sqllm.service

# Ver logs
sudo journalctl -u gl_sqllm.service -f
```

---

## 🔧 Dependências Principais

### Dependências de Produção

```
streamlit               # Framework web
google-cloud-bigquery   # Acesso ao BigQuery
google-generativeai     # API Gemini
pandas                  # Manipulação de dados
plotly                  # Visualizações interativas
duckdb                  # Cache local
sentence-transformers   # Embeddings para RAG
annoy                   # Índice vetorial
```

Para versões específicas, veja `requirements.txt`:

```bash
cat requirements.txt
```

---

## 🧠 Sistema RAG (Retrieval-Augmented Generation)

### Como Funciona

1. **RAG Manager** (`rag_system/manager.py`) - Singleton centralizado
   - Carrega `tables_config.json` com multi-path lookup
   - Inicializa RAG v3 com validação de embeddings
   - Em dev mode: detecta mudanças e recarrega automaticamente

2. **RAG v3** (`rag_system/business_metadata_rag_v3.py`) - Multi-factor scoring
   - Scoring em 5 dimensões: semântica, keywords, domínio, temporal, métricas
   - Pré-computa embeddings com `sentence-transformers`
   - Identifica melhor tabela para pergunta do usuário

3. **Fallback RAG v2** - Para compatibilidade
   - Índice Annoy com cache
   - Busca vetorial rápida

### Auto-reload em Desenvolvimento

```bash
export ENVIRONMENT=dev
# Editar config/tables_config.json → RAG recarrega automaticamente
vim config/tables_config.json
```

---

## 📊 Google Cloud Setup

### Criar Projeto GCP

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie novo projeto
3. Habilite APIs:
   - BigQuery API
   - Generative AI API
4. Crie Service Account com permissões BigQuery
5. Baixe JSON e salve como `config/gl.json`

### Estrutura BigQuery Esperada

```sql
-- Dataset contendo suas tabelas
CREATE DATASET IF NOT EXISTS seu_dataset;

-- Exemplo de tabela
CREATE TABLE seu_dataset.drvy_VeiculosVendas (
  data_venda DATE,
  tipo_veiculo STRING,
  valor_venda FLOAT64,
  ...
);

-- Tabela de logs do sistema (automática)
CREATE TABLE seu_dataset.sqllm_logs (
  timestamp TIMESTAMP,
  user_id STRING,
  pergunta STRING,
  sql_gerada STRING,
  resultado JSON,
  ...
);
```

---

## 🐛 Troubleshooting

### Erro: `DefaultCredentialsError: File gl.json was not found`

**Solução:** 
- Verificar se `config/gl.json` existe
- Verificar permissões: `ls -la config/gl.json`
- Se não existir, baixe do Google Cloud Console

```bash
ls -la config/gl.json
```

### Erro: `Config não encontrado: tables_config.json`

**Solução:**
- Arquivo deve estar em `config/tables_config.json`
- Sistema procura em múltiplas localizações automaticamente
- Verificar path: `cat config/tables_config.json | head`

### RAG não inicializa

**Solução:**
- Verificar `config/tables_config.json` é JSON válido
- Verificar `sentence-transformers` instalado: `pip list | grep sentence`
- Ver logs: `tail -50 /var/log/syslog`

### Cache.db permission denied

**Solução:**
```bash
# Corrigir permissões
sudo chown $USER:$USER cache.db
chmod 666 cache.db
```

---

## 📈 Arquitetura de Fluxo

```
PERGUNTA EM PORTUGUÊS
        ↓
    RAG SYSTEM
        ├─ RAG v3 (identificar tabela)
        └─ RAG Padrões (padrões SQL)
        ↓
  GEMINI API
        ├─ Extrai parâmetros
        └─ Gera função SQL
        ↓
  BUILD QUERY
        ├─ Valida parâmetros
        └─ Monta SQL final
        ↓
 BIGQUERY EXECUTE
        ├─ Executa query
        └─ Retorna resultados
        ↓
    ANÁLISE GEMINI
        ├─ Interpreta dados
        ├─ Gera gráficos
        └─ Resume insights
        ↓
   RESPOSTA AO USUÁRIO
```

---

## 🔍 Multi-path Lookup Pattern

Sistema de busca de arquivos em múltiplas localizações (implementado em todos os módulos):

```python
possible_paths = [
    "config/arquivo.json",           # Primeira escolha (recomendado)
    "../config/arquivo.json",        # Relativa ao módulo
    "arquivo.json",                  # Raiz/cwd
]

for path in possible_paths:
    if os.path.exists(path):
        return path
```

Garante funcionamento independente do local de execução!

---

## 📞 Suporte

- **Issues:** GitHub Issues
- **Documentação:** Este README
- **Logs:** `sudo journalctl -u gl_sqllm.service -f`
- **Teste direto:** `python tests/test_backend_flow.py`

---

## 📝 Licença

Projeto proprietário. Todos os direitos reservados.

---

## ✨ Features Principais

- ✅ Conversão automática NL → SQL via Gemini
- ✅ RAG inteligente para seleção de tabelas
- ✅ Cache distribuído com DuckDB
- ✅ Validação de queries com Gemini
- ✅ Análise de resultados automática
- ✅ Geração de gráficos interativos
- ✅ Sistema de rate limiting
- ✅ Autenticação de usuários
- ✅ Logging completo em BigQuery
- ✅ Deploy como serviço systemd

---

**Última atualização:** Novembro 2025
**Versão:** 3.0 (Reorganizada com multi-path lookup)
