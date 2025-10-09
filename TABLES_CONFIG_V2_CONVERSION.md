# ATUALIZAÇÃO TABLES_CONFIG COPY.JSON - ESTRUTURA V2

## Conversão Realizada
Atualizei o arquivo `tables_config copy.json` para usar a mesma estrutura organizada e detalhada do `tables_config.json` (formato v2).

## Estrutura v2 Implementada

### 📋 **metadata**
- `table_id`: Identificador da tabela
- `bigquery_table`: Nome completo no BigQuery
- `description`: Descrição detalhada da funcionalidade
- `domain`: Domínio de negócio (vendas_automotivas, consorcio, financeiro_contabil)
- `last_updated`: Data da última atualização

### 🔧 **business_rules**
- `critical_rules`: Regras fundamentais com alta prioridade
- `query_rules`: Regras específicas para construção de queries

### 📊 **fields** (Organizados por Categoria)
- `temporal_fields`: Campos de data/tempo com extrações comuns
- `dimension_fields`: Dimensões para agrupamento e filtros
- `metric_fields`: Métricas para agregações
- `filter_fields`: Campos auxiliares para filtros

### 💡 **usage_examples**
- `ranking_queries`: Exemplos de rankings e top N
- `temporal_analysis`: Análises temporais e comparações
- `search_examples`: Exemplos de buscas e filtros
- `value_analysis`: Análises de valores monetários
- `variance_analysis`: Análises de variação (específico para dados financeiros)

## Tabelas Convertidas

### 1. **drvy_VeiculosVendas** (Vendas de Veículos)
- **Domain**: vendas_automotivas
- **Campos principais**: dta_venda, modelo, cidade, val_total, QTE
- **Regras especiais**: Negocio_CC para filtro motos/carros, LIKE para buscas textuais
- **Exemplos**: Rankings por vendedor, comparações temporais, análises por modelo

### 2. **dvry_ihs_cotas_ativas** (Consórcio Ativo)
- **Domain**: consorcio
- **Campos principais**: Data_da_Venda, Vendedor, Modelo, COUNT(*)
- **Regras especiais**: Conversão de datas STRING para DATE, percentual como faixa
- **Exemplos**: Top vendedores, análises por UF, contratos por modelo

### 3. **dvry_ihs_qualidade_vendas_historico** (Histórico Consórcio)
- **Domain**: consorcio_historico
- **Campos principais**: Dt_Venda, Nome_do_Vendedor, Plano, Tipo_de_Contrato
- **Regras especiais**: Conversão de data, buscas por múltiplos planos
- **Exemplos**: Vendas por vendedor, planos mais vendidos

### 4. **api_webservice_plano** (Financeiro)
- **Domain**: financeiro_contabil
- **Campos principais**: ANO, MES, VALOR_ORCADO, VALOR_REALIZADO
- **Regras especiais**: Campos temporais como INTEGER, análise de variação
- **Exemplos**: Comparativo orçado vs realizado, análise por conta contábil

## Benefícios da Estrutura v2

### 🎯 **Organização Melhorada**
- Metadados claros para cada tabela
- Campos categorizados por função
- Regras de negócio estruturadas por prioridade

### 🚀 **Compatibilidade RAG**
- Estrutura otimizada para o sistema RAG
- Contexto mais rico para geração de SQL
- Exemplos práticos para orientar o modelo

### 📈 **Manutenibilidade**
- Fácil identificação de campos por categoria
- Regras de negócio centralizadas
- Exemplos reutilizáveis

### 🔍 **Melhor Precisão**
- Patterns de busca padronizados
- Agregações sugeridas por campo
- Regras específicas por domínio

## Status: ✅ CONCLUÍDO

Todas as 4 tabelas foram successfully convertidas para a estrutura v2:
- JSON válido e bem formado
- Todas as seções obrigatórias presentes
- Informações originais preservadas e organizadas
- Compatível com o sistema RAG existente

O arquivo `tables_config copy.json` agora está alinhado com a estrutura moderna e pode ser usado diretamente no sistema!