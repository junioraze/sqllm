"""
Teste completo do RAG local com sentence-transformers
- Carrega e atualiza o cache de metadados
- Mostra as tabelas e embeddings no banco
- Testa perguntas e salva contexto retornado com diferentes thresholds e max_results em JSON estruturado
"""
import duckdb
import json
from business_metadata_rag import BusinessMetadataRAGV2

def get_contexts_for_query(rag, pergunta, max_results_list, thresholds):
    resultados = []
    for max_results in max_results_list:
        for threshold in thresholds:
            ctxs = rag.retrieve_relevant_context(pergunta, max_results=max_results, similarity_threshold=threshold)
            resultados.append({
                "max_results": max_results,
                "similarity_threshold": threshold,
                "contexts": ctxs if ctxs else [],
            })
    return resultados

def main():
    # 1. Atualiza o cache de metadados e embeddings
    rag = BusinessMetadataRAGV2()
    print("\n=== Atualizando cache de metadados e embeddings ===")
    rag.update_metadata_cache()

    # 2. Mostra tabelas e embeddings no banco
    tabelas_info = []
    with duckdb.connect(rag.cache_db_path) as conn:
        try:
            tables = conn.execute("SELECT table_name, description FROM business_metadata_v2").fetchall()
            for t in tables:
                tabelas_info.append({"table_name": t[0], "description": t[1]})
            emb_count = conn.execute("SELECT COUNT(*) FROM business_embeddings_v2").fetchone()[0]
        except Exception as e:
            tabelas_info.append({"erro": str(e)})
            emb_count = None

    # 3. Testa perguntas e salva contexto retornado
    perguntas = [
        "vendas de veículos",
        "contratos de consórcio ativos",
        "histórico de vendas de cotas",
        "dados financeiros e orçamento",
        "clientes inadimplentes",
        "planos de pagamento",
        "comparação de venda de veiculos"
    ]

    max_results_list = [1, 2, 3]
    thresholds = [0.05, 0.15, 0.3]

    resultado_final = {
        "tabelas": tabelas_info,
        "total_embeddings": emb_count,
        "testes": []
    }

    for pergunta in perguntas:
        teste = {
            "pergunta": pergunta,
            "rag_contexts": get_contexts_for_query(rag, pergunta, max_results_list, thresholds)
        }
        # 4. Testa integração com orientação SQL
        try:
            from sql_pattern_rag import get_sql_guidance_for_query
            sql_orientacoes = get_sql_guidance_for_query(pergunta)
            teste["sql_guidance"] = sql_orientacoes
        except Exception as e:
            teste["sql_guidance"] = f"[ERRO] {e}"
        resultado_final["testes"].append(teste)

    # 5. Salva resultado em JSON
    with open("teste_rag_result.json", "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=2)
    print("\n[LOG] Resultados dos testes salvos em teste_rag_result.json")

if __name__ == "__main__":
    main()
