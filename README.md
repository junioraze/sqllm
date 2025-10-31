# SQLLM — Sistema de Análise de Dados com IA

Sistema avançado que converte linguagem natural em consultas SQL usando IA (Google Gemini) com interface web Streamlit. O sistema é modular, seguro e altamente configurável para diferentes domínios de negócio.
---

## 📁 Arquivos de Configuração do Sistema

### 1. `config.py`
Arquivo central de configuração. Carrega variáveis do `.env`, configurações do cliente (`client_config.json`) e das tabelas (`tables_config.json`). Define mensagens padrão de erro e funções utilitárias para modo empresarial.

### 2. `client_config.json`
Personaliza a interface, exemplos, domínio de negócio e limitações do sistema para cada cliente. Define título, subtítulo, exemplos de perguntas, restrições e mensagem padrão de erro.

### 3. `credentials.json`
Arquivo de autenticação simples para homologação. Utilizado apenas para testes locais, contém dados mínimos para login ou integração básica. Não possui mecanismos avançados de segurança e não deve ser usado em produção. Nunca versionar em repositórios públicos.

### 4. `payment_config.json`
Configura credenciais, URLs, parâmetros de pagamento e planos de assinatura. Utilizado para integração com MercadoPago, controle de limites e funcionalidades de cada plano.

### 5. `requirements.txt`
Lista todas as dependências Python necessárias para rodar o sistema.

---

## 📁 Arquivos de Contexto para o Modelo (Geração de SQL)

### 1. `sql_patterns.json`
Arquivo central que define todos os padrões de queries SQL que o sistema pode gerar. Cada padrão é um objeto com:
- `description`: Explica o objetivo e as regras do padrão.
- `keywords`: Palavras-chave que ativam o padrão.
- `pattern_type`: Tipo do padrão (ex: cte_group_comparison, cte_simple_count, cte_ranking, etc).
- `variables`: Variáveis a serem substituídas no template.
- `sql_template`: Template SQL parametrizado (pode ser omitido se o padrão for mais complexo).
- `example`: Exemplo concreto de uso.
- `function_call_example`: Estrutura de chamada do padrão pelo sistema (campos, CTEs, filtros, ordenação).
- `use_cases`: Casos de uso típicos.

**Exemplo real de padrão:**
```json
{
  "description": "Comparação entre grupos/categorias usando CTEs...",
  "keywords": ["maior que", "superou", "comparar X com Y", ...],
  "pattern_type": "cte_group_comparison",
  "variables": ["period_field", "group_field", "value_field", "table", "filters", "group_x", "group_y"],
  "function_call_example": {
    "select": ["mes", "valor_{city1}", "valor_{city2}"],
    "cte": "WITH cte_limpeza AS (...) ...",
    "from_table": "cte_comparacao",
    "order_by": ["mes"]
  },
  "use_cases": ["em quais meses as vendas de Crato superaram Salvador"]
}
```

**Boas práticas ao editar:**
- Sempre explique claramente a lógica e as restrições do padrão.
- Inclua exemplos reais e casos de uso.
- Mantenha o template SQL aderente às melhores práticas do BigQuery.
- Atualize as palavras-chave para garantir boa cobertura sem ambiguidade.
- Siga as regras de CTE e nomenclatura descritas em `bigquery_best_practices` dentro do próprio arquivo.
- Nunca insira comentários no SQL gerado.

**Lista dos principais padrões disponíveis:**
- `group_comparison`: Comparação entre grupos/categorias usando CTEs.
- `simple_count_cte`: Contagem simples de registros com CTE de limpeza.
- `top_n_ranking_with_cte`: Ranking top N com CTE de agregação e filtro.
- `temporal_comparison_cte`: Comparação temporal multi-período.
- `percentage_breakdown_cte`: Análise de participação percentual.
- `growth_analysis_cte`: Análise de crescimento ano a ano.
- `text_search_complex_cte`: Busca textual complexa com múltiplos filtros.
- `regional_analysis_cte`: Análise regional combinando vendas e métricas socioeconômicas.
- `monthly_trend_detailed_cte`: Tendências mensais detalhadas.
- `customer_analysis_cte`: Segmentação e análise de clientes.

**Regras críticas e melhores práticas (extraídas do próprio arquivo):**
- SEMPRE use CTEs para organizar queries complexas, cada CTE com responsabilidade única.
- CTE de limpeza: apenas conversões (CAST, EXTRACT, UPPER, etc).
- CTE de agregação: SUM, COUNT, AVG com GROUP BY.
- CTE de análise: cálculos finais, rankings, comparações.
- NUNCA misture transformação e análise na mesma CTE.
- Use nomes descritivos para CTEs.
- Para buscas textuais: UPPER(campo) LIKE UPPER('%valor%').
- Para rankings: crie o campo analítico (ROW_NUMBER, RANK, etc) na CTE e filtre no SELECT final usando WHERE ranking <= N.
- Prefira CTEs sobre subqueries aninhadas para melhor legibilidade.
- Nunca insira comentários (-- ou /**/ ou qualquer que seja) no código gerado.

**Como editar/adicionar padrões:**
- Siga o modelo dos padrões existentes.
- Explique claramente o objetivo, regras e variáveis.
- Teste as alterações executando perguntas relacionadas na interface do sistema.

---

### 2. `tables_config.json`
Arquivo que descreve as tabelas do banco de dados, campos, tipos, regras de negócio e exemplos de queries. Cada tabela possui:
- `metadata`: Informações como nome, descrição, domínio, última atualização e referência BigQuery.
- `business_rules`: Regras críticas e de consulta (ex: sempre usar QTE para contagem, nunca usar LIMIT com QUALIFY).
- `fields`: Campos divididos em temporais, dimensionais, métricas e filtros, com tipos, descrições, exemplos e padrões de busca.
- `usage_examples`: Exemplos reais de perguntas e queries SQL.

**Exemplo real de estrutura:**
```json
{
  "metadata": {
    "table_id": "ecPedidosVenda",
    "bigquery_table": "bigquery-for-ml.apecommerce.ecPedidosVenda",
    "description": "Tabela principal de pedidos de e-commerce...",
    "domain": "ecommerce_vendas",
    "last_updated": "2025-10-09"
  },
  "business_rules": {
    "critical_rules": [ ... ],
    "query_rules": [ ... ]
  },
  "fields": {
    "temporal_fields": [ ... ],
    "dimension_fields": [ ... ],
    "metric_fields": [ ... ],
    "filter_fields": [ ... ]
  },
  "usage_examples": [ ... ]
}
```

**Boas práticas ao editar:**
- Atualize descrições e regras sempre que houver mudança de negócio.
- Inclua exemplos de queries para cada novo campo ou métrica.
- Siga o padrão de nomenclatura e tipos para garantir integração com o sistema.
- Use sempre os padrões de busca e conversão recomendados (ex: UPPER + LIKE para texto, SAFE_CAST para datas).

**Exemplo de uso real:**
Pergunta: "Top 5 lojas por volume de vendas"
```json
{
  "select": ["pedido_sg_loja", "total_sales_volume"],
  "order_by": ["total_sales_volume DESC"],
  "limit": 5,
  "cte": "WITH cte_agregacao AS (SELECT pedido_sg_loja, SUM(valorLInhaPedidoNF) AS total_sales_volume FROM ecPedidosVenda GROUP BY pedido_sg_loja)",
  "from_table": "cte_agregacao"
}
```
SQL gerado:
```sql
WITH cte_agregacao AS (SELECT pedido_sg_loja, SUM(valorLInhaPedidoNF) AS total_sales_volume FROM ecPedidosVenda GROUP BY pedido_sg_loja)
SELECT pedido_sg_loja, total_sales_volume FROM cte_agregacao ORDER BY total_sales_volume DESC LIMIT 5;
```

---

## 📁 Regras, Práticas e Fluxos do Sistema

- Todas as queries geradas seguem as regras de CTE, nomenclatura e boas práticas do BigQuery.
- O sistema utiliza RAG duplo: Business RAG (metadados e regras de negócio) e SQL Pattern RAG (templates SQL e melhores práticas).
- Visualização automática: Geração de gráficos a partir dos resultados, conforme regras do arquivo `sql_patterns.json`.
- Cache multinível: DuckDB e memória para performance.
- Autenticação, rate limiting e compliance.

---

## 📚 Templates e Guia para Arquivos de Configuração

### 1. Como criar e manter o `tables_config.json`

Este arquivo define o esquema, regras e exemplos de uso para cada tabela do projeto. Siga o template abaixo para criar novas tabelas ou editar existentes:

```json
{
  "nomeDaTabela": {
    "metadata": {
      "table_id": "nomeDaTabela",
      "bigquery_table": "projeto.dataset.nomeDaTabela",
      "description": "Descrição detalhada da tabela.",
      "domain": "dominio_negocio",
      "last_updated": "YYYY-MM-DD"
    },
    "business_rules": {
      "critical_rules": [
        {
          "rule": "Regra crítica",
          "priority": "alta",
          "context": "Contexto de aplicação"
        }
      ],
      "query_rules": [
        {
          "rule": "Regra de query",
          "context": "Contexto de aplicação"
        }
      ]
    },
    "fields": {
      "temporal_fields": [
        {
          "name": "campo_data",
          "type": "DATE",
          "description": "Data do evento",
          "conversion": "SAFE_CAST(campo_data AS DATE)"
        }
      ],
      "dimension_fields": [
        {
          "name": "campo_categoria",
          "type": "STRING",
          "description": "Categoria do evento"
        }
      ],
      "metric_fields": [
        {
          "name": "campo_valor",
          "type": "FLOAT64",
          "description": "Valor do evento",
          "aggregations": ["SUM", "AVG"]
        }
      ],
      "filter_fields": [
        {
          "name": "campo_filtro",
          "type": "STRING",
          "description": "Filtro de evento"
        }
      ]
    },
    "usage_examples": [
      {
        "question": "Exemplo de pergunta",
        "function_call_example": {
          "select": ["campo_categoria", "campo_valor"],
          "order_by": ["campo_valor DESC"],
          "limit": 5,
          "cte": "WITH cte_agregacao AS (SELECT campo_categoria, SUM(campo_valor) AS campo_valor FROM nomeDaTabela GROUP BY campo_categoria)",
          "from_table": "cte_agregacao"
        },
        "sql_example": "WITH cte_agregacao AS (SELECT campo_categoria, SUM(campo_valor) AS campo_valor FROM nomeDaTabela GROUP BY campo_categoria) SELECT campo_categoria, campo_valor FROM cte_agregacao ORDER BY campo_valor DESC LIMIT 5;"
      }
    ]
  }
}
```

**Boas práticas:**
- Use apenas nomes de campos presentes no BigQuery.
- Documente regras críticas e exemplos reais.
- Atualize `last_updated` sempre que alterar a estrutura.
- Para múltiplas tabelas, adicione novas chaves no topo do JSON.

---

### 2. Como criar e manter o `sql_patterns.json`

Este arquivo centraliza padrões de queries SQL, templates, exemplos e regras para orientar o modelo Gemini e o pipeline.

```json
{
  "sql_patterns": {
    "simple_count_cte": {
      "description": "Contagem simples usando CTE.",
      "keywords": ["contar", "quantidade"],
      "pattern_type": "cte_simple_count",
      "variables": ["table", "filters", "count_field"],
      "sql_template": "WITH cte_limpeza AS (SELECT {count_field} FROM {table} WHERE {filters}) SELECT COUNT({count_field}) AS total_registros FROM cte_limpeza",
      "example": "WITH cte_limpeza AS (SELECT id FROM tabela WHERE status = 'ATIVO') SELECT COUNT(id) AS total_registros FROM cte_limpeza",
      "function_call_example": {
        "select": ["total_registros"],
        "cte": "WITH cte_limpeza AS (SELECT id FROM tabela WHERE status = 'ATIVO')",
        "from_table": "cte_limpeza",
        "order_by": []
      },
      "use_cases": ["contar registros ativos"]
    }
  },
  "bigquery_best_practices": {
    "cte_guidelines": [
      "SEMPRE use CTEs para organizar queries complexas.",
      "Nunca insira comentários no código gerado."
    ],
    "performance_tips": [
      "Prefira CTEs sobre subqueries aninhadas.",
      "Use UPPER(campo) LIKE UPPER('%valor%') para buscas case-insensitive."
    ],
    "common_mistakes": [
      "Misturar transformação e análise na mesma CTE.",
      "Esquecer GROUP BY quando usar agregações."
    ],
    "critical_rules": [
      "TOP 5 como padrão quando não especificado número no ranking.",
      "Nunca insira comentários no código gerado."
    ]
  },
  "chart": {
    "description": "Geração de gráfico a partir do resultado da consulta SQL.",
    "template": "GRAPH-TYPE: {graph_type} | X-AXIS: {x_axis} | Y-AXIS: {y_axis} | COLOR: {color}",
    "rules": [
      "Para comparações temporais: GRAPH-TYPE: line | X-AXIS: periodo | Y-AXIS: valor | COLOR: serie"
    ]
  }
}
```

**Boas práticas:**
- Adicione novos padrões conforme surgirem novos tipos de perguntas.
- Inclua exemplos reais e templates parametrizados.
- Documente variáveis e casos de uso para cada padrão.
- Atualize as seções de boas práticas e erros comuns conforme o projeto evolui.
- Nunca insira comentários SQL nos templates.

---

> **Referências:**
> - As seções 1 e 2 deste README agora apontam para os templates e instruções acima. Sempre consulte esta seção ao criar ou alterar os arquivos `tables_config.json` e `sql_patterns.json`.