"""
Teste completo do RAG local com sentence-transformers
- Carrega e atualiza o cache de metadados
- Mostra as tabelas e embeddings no banco
- Testa perguntas e mostra contexto retornado
"""
import duckdb
from business_metadata_rag import BusinessMetadataRAGV2, get_optimized_business_context

# 1. Atualiza o cache de metadados e embeddings
rag = BusinessMetadataRAGV2()
print("\n=== Atualizando cache de metadados e embeddings ===")
rag.update_metadata_cache()

# 2. Mostra tabelas e embeddings no banco
print("\n=== Tabelas no banco de metadados ===")
with duckdb.connect(rag.cache_db_path) as conn:
    tables = conn.execute("SELECT table_name, description FROM business_metadata_v2").fetchall()
    for t in tables:
        print(f"- {t[0]}: {t[1]}")
    print("\n=== Embeddings salvos ===")
    emb_count = conn.execute("SELECT COUNT(*) FROM business_embeddings_v2").fetchone()[0]
    print(f"Total de embeddings: {emb_count}")

# 3. Testa perguntas e mostra contexto retornado
perguntas = [
    "vendas de veículos",
    "contratos de consórcio ativos",
    "histórico de vendas de cotas",
    "dados financeiros e orçamento",
    "clientes inadimplentes",
    "planos de pagamento",
    "comparação de venda de veiculos"
]

from sql_pattern_rag import get_sql_guidance_for_query

for pergunta in perguntas:
    print(f"\n--- Pergunta: '{pergunta}' ---")
    contexto = get_optimized_business_context(pergunta, max_results=2)
    print("[RAG - Metadados de Negócio]")
    print(contexto)
    print("[RAG - Padrões SQL]")
    sql_orientacoes = get_sql_guidance_for_query(pergunta)
    print(sql_orientacoes)
