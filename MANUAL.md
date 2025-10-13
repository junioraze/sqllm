# Manual de Utilização do SQLLM

## 1. Visão Geral do Projeto

O SQLLM é um sistema de análise de dados com IA, focado em transformar perguntas em linguagem natural em queries SQL otimizadas para BigQuery, utilizando técnicas avançadas de RAG (Retrieval-Augmented Generation) e integração com o Google Gemini. O sistema é altamente configurável, permitindo que usuários avancem a aplicação alterando arquivos de referência para padrões SQL e metadados de tabelas.

Principais componentes:
- **Conversão de perguntas em SQL** com contexto de negócio e padrões otimizados.
- **RAG Duplo**: Business RAG (metadados e regras de negócio) e SQL Pattern RAG (templates SQL e melhores práticas).
- **Visualização automática**: Geração de gráficos a partir dos resultados.
- **Cache multinível**: DuckDB e memória para performance.
- **Autenticação, rate limiting e compliance**.

## 2. Estrutura dos Arquivos de Referência

### 2.1. `sql_patterns.json`

Este arquivo define os padrões de queries SQL que o modelo utiliza para gerar respostas. Cada padrão possui:
- `description`: Explica o objetivo e as regras do padrão.
- `keywords`: Palavras-chave que ativam o padrão.
- `pattern_type`: Tipo do padrão (ex: cte_group_comparison, qualify_window_function).
- `variables`: Variáveis a serem substituídas no template.
- `sql_template`: Template SQL parametrizado.
- `example`: Exemplo concreto de uso.
- `use_cases`: Casos de uso típicos.

**Exemplo real:**
```json
{
  "description": "Comparação entre grupos/categorias...",
  "keywords": ["maior que", "superou", ...],
  "pattern_type": "cte_group_comparison",
  "variables": ["period_field", ...],
  "sql_template": "...",
  "example": "WITH vendas_cidade AS (...) ...",
  "use_cases": ["em quais meses as vendas de Crato superaram Salvador"]
}
```

**Boas práticas ao editar:**
- Sempre explique claramente a lógica e as restrições do padrão.
- Inclua exemplos reais e casos de uso.
- Mantenha o template SQL aderente às melhores práticas do BigQuery.
- Atualize as palavras-chave para garantir boa cobertura sem ambiguidade.

### 2.2. `tables_config.json`

Este arquivo descreve as tabelas do banco de dados, campos, tipos, regras de negócio e exemplos de queries. Cada tabela possui:
- `metadata`: Informações como nome, descrição, domínio, última atualização e referência BigQuery.
- `business_rules`: Regras críticas e de consulta (ex: sempre usar QTE para contagem, nunca usar LIMIT com QUALIFY).
- `fields`: Campos divididos em temporais, dimensionais, métricas e filtros, com tipos, descrições, exemplos e padrões de busca.
- `usage_examples`: Exemplos reais de perguntas e queries SQL.

**Exemplo real:**
```json
{
  "metadata": {
    "table_id": "drvy_VeiculosVendas",
    "bigquery_table": "glinhares.delivery.drvy_VeiculosVendas",
    "description": "Tabela principal de vendas de veículos...",
    ...
  },
  "business_rules": {
    "critical_rules": [
      {"rule": "SEMPRE use QTE para contagem de veículos vendidos", ...},
      ...
    ],
    "query_rules": [ ... ]
  },
  "fields": {
    "temporal_fields": [ ... ],
    "dimension_fields": [ ... ],
    "metric_fields": [ ... ],
    "filter_fields": [ ... ]
  },
  "usage_examples": {
    "ranking_queries": [ ... ],
    ...
  }
}
```

**Boas práticas ao editar:**
- Atualize descrições e regras sempre que houver mudança de negócio.
- Inclua exemplos de queries para cada novo campo ou métrica.
- Siga o padrão de nomenclatura e tipos para garantir integração com o sistema.
- Use sempre os padrões de busca e conversão recomendados (ex: UPPER + LIKE para texto, SAFE_CAST para datas).

## 3. Como Alterar e Adicionar Padrões/Tabelas

- Para adicionar um novo padrão SQL, edite `sql_patterns.json` seguindo o modelo dos existentes.
- Para adicionar uma nova tabela, siga a estrutura de `tables_config.json`, preenchendo todos os campos obrigatórios e exemplos.
- Teste as alterações executando perguntas relacionadas na interface do sistema.

## 4. Integração do VS Code com GCP Compute Engine via SSH


### Observações Importantes sobre SSH no GCP

1. **Pré-requisitos:**
  - VS Code instalado.
  - Extensão "Remote - SSH" instalada.
  - Google Cloud SDK instalado ([instruções](https://cloud.google.com/sdk/docs/install)).
  - Autentique-se no SDK com:
    ```bash
    gcloud auth login
    ```

2. **Configure o SSH automaticamente para todas as VMs do projeto:**
  Execute o comando abaixo para gerar e atualizar as entradas SSH de todas as VMs que você tem acesso:
  ```bash
  gcloud compute config-ssh --project=SEU-PROJETO
  ```
  Isso irá criar/atualizar o arquivo `~/.ssh/config` com aliases para cada VM, facilitando o acesso.

3. **Ajuste o usuário no arquivo SSH (se necessário):**
  Caso precise, edite o arquivo `~/.ssh/config` para garantir que o campo `User` corresponda ao seu usuário do GCP (normalmente seu e-mail ou nome de usuário configurado pelo SDK).

4. **Conexão pelo VS Code:**
  - No VS Code, pressione `Ctrl+Shift+P` e selecione `Remote-SSH: Connect to Host...`.
  - Use o alias gerado pelo comando anterior (exemplo: `NOME-DA-VM` ou `NOME-DA-VM.ZONA.PROJETO`).
  - Após conectar, navegue até o diretório do projeto e edite os arquivos normalmente.

**Dica:**
Usar o comando `gcloud compute config-ssh` elimina a necessidade de configurar manualmente hosts, portas e chaves, tornando o acesso via plugin Remote-SSH do VS Code muito mais simples e seguro. 
Em seguida acessa ~/.ssh/config e altera o User pro nome do usuario correto
Ex:
`Host tableauconjectovmone.us-east1-d.bigquery-for-ml
    User Junio #aqui vc altera pro nome do seu usuario
    HostName 34.148.80.173
    IdentityFile C:\Users\Junio\.ssh\google_compute_engine
    UserKnownHostsFile=C:\Users\Junio\.ssh\google_compute_known_hosts
    HostKeyAlias=compute.3808280618944019602
    IdentitiesOnly=yes
    CheckHostIP=no
`
## 5. Melhores Práticas e Recomendações

- Sempre utilize CTEs para limpeza/conversão de campos antes da análise.
- Nunca misture transformação e análise na mesma CTE.
- Use QUALIFY ao invés de LIMIT para rankings.
- Prefira aliases descritivos no SELECT final.
- Siga as regras críticas e exemplos de cada tabela para evitar erros de referência e garantir performance.

## 6. Suporte e Contribuição

- Para dúvidas, consulte o README ou abra uma issue.
- Sugestões de melhoria devem ser feitas via Pull Request, seguindo o guia de estilo do projeto.

---

**Última atualização:** Outubro 2025
**Contato:** [email do responsável]
