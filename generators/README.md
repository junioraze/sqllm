# TABLE CONFIG GENERATOR - Documentação

## 📋 Visão Geral

Sistema automático para gerar arquivos `table_config.json` a partir do schema do BigQuery. Ele combina:

1. **Extração de Schema** - Recupera DDL e metadados do BigQuery
2. **Análise de Perfil** - Gera estatísticas sobre as tabelas
3. **Classificação Automática** - Categoriza campos (temporal, dimension, metric, filter)
4. **Refinamento com IA** - Usa Gemini para gerar regras de negócio
5. **Exportação Estruturada** - Salva em formato padronizado

---

## 🚀 Como Usar

### Instalação

Nenhuma dependência adicional além do que já está no projeto.

### Uso Básico

#### 1. Gerar config para uma tabela

```bash
cd /home/Junio/gl_sqllm
python generate_table_config.py drvy_VeiculosVendas
```

**Resultado:**
- `table_config_drvy_VeiculosVendas.json` - Config completo gerado

#### 2. Gerar para múltiplas tabelas

```bash
python generate_table_config.py drvy_VeiculosVendas dvry_ihs_cotas_ativas dvry_ihs_qualidade_vendas_historico
```

Gera 3 arquivos:
- `table_config_drvy_VeiculosVendas.json`
- `table_config_dvry_ihs_cotas_ativas.json`
- `table_config_dvry_ihs_qualidade_vendas_historico.json`

#### 3. Sem refinamento (mais rápido, sem usar Gemini)

```bash
python generate_table_config.py drvy_VeiculosVendas --no-refine
```

---

## 🛠️ Comandos Avançados

### Listar tabelas disponíveis

```bash
python generate_table_config.py --list
```

Mostra todas as tabelas no dataset do BigQuery.

### Validar config gerado

```bash
python generate_table_config.py --validate table_config_drvy_VeiculosVendas.json
```

Valida:
- ✅ Estrutura JSON válida
- ✅ Todas as chaves obrigatórias presentes
- ✅ Campos obrigatórios em metadata
- ✅ Quantidade de campos

### Mesclar múltiplos configs em um único arquivo

```bash
python generate_table_config.py --merge tables_config.json
```

Converte:
```
table_config_drvy_VeiculosVendas.json
table_config_dvry_ihs_cotas_ativas.json
table_config_dvry_ihs_qualidade_vendas_historico.json
                    ↓↓↓
            tables_config.json
```

---

## 📊 Estrutura de Saída

### Arquivo individual: `table_config_<TABLE_ID>.json`

```json
{
  "metadata": {
    "table_id": "drvy_VeiculosVendas",
    "bigquery_table": "glinhares.delivery.drvy_VeiculosVendas",
    "description": "Tabela de vendas de veículos...",
    "domain": "automotivo_vendas",
    "last_updated": "2025-01-20T10:30:00",
    "row_count_sampled": 1000000,
    "keywords": ["veiculo", "vendas", "carro", ...],
    "exclude_keywords": []
  },
  "business_rules": {
    "critical_rules": [
      {
        "rule": "Sempre use QTE para contagem de veículos",
        "priority": "alta",
        "context": "Campo QTE representa quantidade de veículos vendidos"
      }
    ],
    "query_rules": [
      {
        "rule": "Use LIKE UPPER para campos textuais",
        "context": "WHERE UPPER(modelo) LIKE UPPER('%COROLLA%')"
      }
    ]
  },
  "fields": {
    "temporal_fields": [...],
    "dimension_fields": [...],
    "metric_fields": [...],
    "filter_fields": [...]
  },
  "usage_examples": {
    "ranking_queries": [...],
    "temporal_analysis": [...],
    "search_examples": [...],
    "value_analysis": [...],
    "temporal_ranking": [...]
  },
  "profile": {
    "total_rows_sampled": 1000000,
    "timestamp": "2025-01-20T10:30:00"
  }
}
```

### Arquivo mesclado: `tables_config.json`

```json
{
  "drvy_VeiculosVendas": { /* config completo */ },
  "dvry_ihs_cotas_ativas": { /* config completo */ },
  "dvry_ihs_qualidade_vendas_historico": { /* config completo */ }
}
```

---

## 🔄 Workflow Recomendado

### Passo 1: Gerar configs para todas as tabelas

```bash
python generate_table_config.py drvy_VeiculosVendas dvry_ihs_cotas_ativas dvry_ihs_qualidade_vendas_historico
```

### Passo 2: Validar cada config

```bash
python generate_table_config.py --validate table_config_drvy_VeiculosVendas.json
python generate_table_config.py --validate table_config_dvry_ihs_cotas_ativas.json
python generate_table_config.py --validate table_config_dvry_ihs_qualidade_vendas_historico.json
```

### Passo 3: Revisar e refinar manualmente (opcional)

- Abra cada `table_config_*.json`
- Revise as `critical_rules` e `query_rules`
- Adicione mais campos em `usage_examples` se necessário

### Passo 4: Mesclar em um único arquivo

```bash
python generate_table_config.py --merge tables_config_novo.json
```

### Passo 5: Substituir arquivo original

```bash
# Fazer backup do original
cp tables_config.json tables_config_backup_$(date +%Y%m%d_%H%M%S).json

# Usar novo arquivo
cp tables_config_novo.json tables_config.json
```

---

## 📝 O que é Gerado Automaticamente?

### ✅ Gerado pelo Generator

- **Metadata básico**: table_id, description, domain, keywords
- **Schema parsing**: temporal_fields, dimension_fields, metric_fields
- **Profile**: total de linhas, timestamp

### ✅ Gerado pelo Gemini (se --no-refine não for usado)

- **Critical Rules**: Regras críticas de negócio (2-3)
- **Query Rules**: Padrões SQL recomendados (2-3)
- **Keywords extras**: Palavras-chave adicionais para busca

### ⚠️ Precisa de Refinamento Manual

- **Usage Examples**: Exemplos específicos por tipo de análise
- **Conversões complexas**: Transformações de campos especiais
- **Contextos de negócio**: Detalhes muito específicos

---

## 🔧 Customização

### Usar diretório de saída diferente

```bash
python generate_table_config.py drvy_VeiculosVendas --output-dir ./configs
```

### Combinar com outro workflow

```python
from table_config_generator import TableConfigGenerator

generator = TableConfigGenerator()

# Gerar config
config = generator.generate_for_table("drvy_VeiculosVendas", refine=True)

# Modificar manualmente
config['metadata']['keywords'].append('minha_palavra')
config['business_rules']['critical_rules'].append({
    "rule": "Minha regra customizada",
    "priority": "alta",
    "context": "Contexto específico"
})

# Salvar
generator.save_config("drvy_VeiculosVendas", config)
```

---

## 🎯 Exemplo Completo

```bash
# 1. Listar tabelas
python generate_table_config.py --list

# 2. Gerar configs para as 3 principais tabelas
python generate_table_config.py drvy_VeiculosVendas dvry_ihs_cotas_ativas dvry_ihs_qualidade_vendas_historico

# 3. Validar cada uma
python generate_table_config.py --validate table_config_drvy_VeiculosVendas.json
python generate_table_config.py --validate table_config_dvry_ihs_cotas_ativas.json
python generate_table_config.py --validate table_config_dvry_ihs_qualidade_vendas_historico.json

# 4. Mesclar em um único arquivo
python generate_table_config.py --merge tables_config_novo.json

# 5. Fazer backup e substituir
cp tables_config.json tables_config_backup.json
cp tables_config_novo.json tables_config.json

# 6. Testar o sistema com o novo config
python test_backend_flow.py --test-id 1
```

---

## ❓ FAQ

### P: Por que algumas tabelas demoram mais?

**R:** Tabelas muito grandes podem demorar na extração de DDL e no profile. Use `--no-refine` para acelerar.

### P: Posso usar isso para tabelas que não estão em `tables_config.json`?

**R:** Sim! O generator trabalha com qualquer tabela do BigQuery no dataset configurado.

### P: Como adiciono campos manualmente depois?

**R:** Edite o arquivo JSON gerado:
1. Abra `table_config_<table_id>.json`
2. Adicione campos em `fields.dimension_fields` ou `fields.metric_fields`
3. Valide com `--validate`

### P: O Gemini está lento. Posso pular?

**R:** Sim, use `--no-refine`. As regras críticas serão vazias, mas a estrutura base será criada.

### P: Erro: "Table not found"

**R:** Verifique se o table_id está correto com `python generate_table_config.py --list`

---

## 📚 Template de Referência

Ver `table_config_template.json` para estrutura completa e anotações.

---

## 🚀 Integração com o Sistema RAG

Após gerar os configs, o sistema RAG vai automaticamente:

1. **Usar keywords** para busca semântica
2. **Aplicar business rules** nas queries
3. **Converter campos** conforme especificado
4. **Validar fields** contra o schema definido

```python
# Exemplo no RAG v3
rag = BusinessMetadataRAGv3()
best_table = rag.get_best_table("vendas de carros em 2024")
# Usa keywords e metadata de table_config.json para identificar
```

---

## 📞 Troubleshooting

| Erro | Solução |
|------|---------|
| `Table not found` | Verifique table_id com `--list` |
| `JSON inválido` | Rode `--validate` para encontrar erros |
| `Gemini timeout` | Use `--no-refine` |
| `Missing table_id` | Config não tem `metadata.table_id` |
| `BigQuery error` | Verifique credenciais e permissões |

