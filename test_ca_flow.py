#!/usr/bin/env python3
"""
Script de teste do fluxo Conversational Analytics
Testa 3 perguntas e valida se tabela + gráfico são retornados
"""

import sys
sys.path.insert(0, '/home/Junio/gl_sqllm')

from conversational_analytics_handler import ConversationalAnalyticsHandler

# Configurações das MUITAS perguntas de teste com variações
TEST_QUESTIONS = [
    # Perguntas sobre estado
    "Quantos veículos foram vendidos no Ceará?",
    "Qual o total vendido em São Paulo?",
    "Mostre vendas por estado",
    
    # Perguntas sobre ranking
    "Quais são os TOP 3 modelos?",
    "Ranking dos 5 melhores modelos",
    "Principais modelos vendidos",
    
    # Perguntas sobre evolução
    "Demonstre evolução de vendas 2023 2024",
    "Comparação de vendas por modelo",
    "Mostre o desempenho em 2024",
]

def print_header(text):
    """Imprime header formatado"""
    print(f"\n{'='*100}")
    print(f"  {text}")
    print(f"{'='*100}\n")

def test_ca_handler():
    """Testa o handler CA com 3 perguntas"""
    
    print_header("TESTE DO FLUXO CONVERSATIONAL ANALYTICS")
    
    try:
        # Inicializa handler
        print("🔧 Inicializando ConversationalAnalyticsHandler...")
        handler = ConversationalAnalyticsHandler(user_id="test_user")
        print("✅ Handler inicializado com sucesso\n")
        
        results = []
        
        for idx, question in enumerate(TEST_QUESTIONS, 1):
            print_header(f"TESTE {idx}/3: {question}")
            
            try:
                # Executa handler
                print(f"📝 Pergunta: {question}\n")
                print("🚀 Processando com CA Handler...")
                summary, tech_details = handler.process(question)
                
                # Validações
                print("\n✅ VALIDAÇÕES:")
                
                # 1. Summary
                summary_ok = summary and len(summary) > 0
                print(f"  ✅ Summary existe: {summary_ok} ({len(summary)} chars)")
                
                # 2. Tech details
                tech_ok = tech_details and isinstance(tech_details, dict)
                print(f"  ✅ Tech details existe: {tech_ok}")
                
                # 3. AgGrid data (tabela)
                aggrid_data = tech_details.get("aggrid_data", []) if tech_ok else []
                aggrid_ok = aggrid_data and len(aggrid_data) > 0
                print(f"  ✅ AgGrid data (tabela): {aggrid_ok} ({len(aggrid_data)} linhas)")
                
                # 4. Chart info (gráfico)
                chart_info = tech_details.get("chart_info") if tech_ok else None
                chart_ok = chart_info is not None and chart_info.get("fig") is not None
                print(f"  ✅ Chart info (gráfico): {chart_ok}")
                
                # 5. Conversational Analytics flag
                is_ca = tech_details.get("conversational_analytics", False) if tech_ok else False
                print(f"  ✅ Response type (CA): {is_ca}")
                
                # Status geral
                all_ok = summary_ok and tech_ok and aggrid_ok and chart_ok
                status = "✅ PASSOU" if all_ok else "❌ FALHOU"
                print(f"\n{status}")
                
                # Armazena resultado
                results.append({
                    "pergunta": question,
                    "status": status,
                    "summary": summary[:150] + "..." if len(summary) > 150 else summary,
                    "tabela_linhas": len(aggrid_data),
                    "grafico_criado": chart_ok,
                    "tech_details_keys": list(tech_details.keys()) if tech_ok else []
                })
                
                # Exibe amostra da resposta
                print(f"\n📊 RESPOSTA (primeiros 200 chars):")
                print(f"   {summary[:200]}...")
                
                if aggrid_data:
                    print(f"\n📋 PRIMEIROS DADOS DA TABELA:")
                    first_row = aggrid_data[0]
                    for key, value in list(first_row.items())[:3]:
                        print(f"   - {key}: {value}")
                
                print("")
                
            except Exception as e:
                import traceback
                print(f"❌ ERRO nesta pergunta: {e}")
                traceback.print_exc()
                results.append({
                    "pergunta": question,
                    "status": "❌ ERRO",
                    "erro": str(e)
                })
        
        # RESUMO FINAL
        print_header("RESUMO DOS TESTES")
        
        for idx, result in enumerate(results, 1):
            print(f"Teste {idx}: {result['status']}")
            print(f"  Pergunta: {result['pergunta']}")
            if "erro" in result:
                print(f"  Erro: {result['erro']}")
            else:
                print(f"  Tabela: {result['tabela_linhas']} linhas")
                print(f"  Gráfico: {result['grafico_criado']}")
            print("")
        
        # Score final
        passed = sum(1 for r in results if "PASSOU" in r['status'])
        total = len(results)
        print(f"SCORE FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! CA está funcionando corretamente.")
        else:
            print(f"⚠️  {total - passed} teste(s) falharam. Verifique os logs acima.")
        
        print_header("FIM DO TESTE")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ca_handler()
    sys.exit(0 if success else 1)
