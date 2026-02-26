#!/usr/bin/env python3
"""
Validação do fluxo Conversational Analytics
Testa integração completa sem Streamlit
"""

import sys
import json
from conversational_analytics_handler import ConversationalAnalyticsHandler

def validate_ca_flow():
    """Valida o fluxo completo do Conversational Analytics."""
    print("=" * 70)
    print("🔍 VALIDAÇÃO DO FLUXO CONVERSATIONAL ANALYTICS")
    print("=" * 70)
    
    # Teste 1: Natura Detection
    print("\n1️⃣  Testando detecção de Natura...")
    handler = ConversationalAnalyticsHandler(user_id="test_user")
    
    test_question = "quais os 5 assuntos mais falados em 2024 para a empresa natura?"
    data_source = handler._detect_data_source(test_question)
    
    print(f"   Pergunta: {test_question}")
    print(f"   Fonte detectada: {data_source}")
    assert data_source == "natura", f"❌ Esperava 'natura', recebeu '{data_source}'"
    print("   ✅ Detecção correta!")
    
    # Teste 2: Limite Extraction
    print("\n2️⃣  Testando extração de limite...")
    limit = handler._extract_limit(test_question)
    print(f"   Limite extraído: {limit}")
    assert limit == 5, f"❌ Esperava 5, recebeu {limit}"
    print("   ✅ Extração correta!")
    
    # Teste 3: Process Natura
    print("\n3️⃣  Testando processamento de Natura...")
    response_dict = handler._process_natura(test_question, limit=5)
    
    assert "summary" in response_dict, "❌ 'summary' não encontrado"
    assert "sql_query" in response_dict, "❌ 'sql_query' não encontrado"
    assert "data_preview" in response_dict, "❌ 'data_preview' não encontrado"
    assert "has_chart" in response_dict, "❌ 'has_chart' não encontrado"
    
    print(f"   ✅ Resposta estruturada corretamente")
    print(f"   - Resumo: {response_dict['summary'][:60]}...")
    print(f"   - Dados: {len(response_dict['data_preview'])} registros")
    print(f"   - Gráfico: {response_dict['has_chart']}")
    
    # Teste 4: Full Process
    print("\n4️⃣  Testando processo completo...")
    try:
        summary, tech_details = handler.process(test_question)
        
        assert isinstance(summary, str), "❌ Summary não é string"
        assert isinstance(tech_details, dict), "❌ tech_details não é dict"
        assert tech_details.get("response_type") == "conversational_analytics", "❌ response_type incorreto"
        assert tech_details.get("chart_info"), "❌ chart_info não está presente"
        assert tech_details["chart_info"].get("fig"), "❌ Figure não foi gerada"
        
        print(f"   ✅ Processo completo executado com sucesso")
        print(f"   - Resposta: {summary[:80]}...")
        print(f"   - Fonte: {tech_details.get('data_source')}")
        print(f"   - Gráfico: {'✓' if tech_details['chart_info'].get('fig') else '✗'}")
        print(f"   - SQL Query: {len(tech_details.get('query', '')) > 0} caracteres")
        
    except Exception as e:
        print(f"   ❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Teste 5: Google Trends Detection
    print("\n5️⃣  Testando detecção de Google Trends...")
    trends_question = "quais são os termos mais populares no google trends agora?"
    trends_source = handler._detect_data_source(trends_question)
    print(f"   Pergunta: {trends_question}")
    print(f"   Fonte detectada: {trends_source}")
    assert trends_source == "google_trends", f"❌ Esperava 'google_trends', recebeu '{trends_source}'"
    print("   ✅ Detecção correta!")
    
    # Teste 6: Data Structure Validation
    print("\n6️⃣  Validando estrutura de tech_details...")
    required_keys = ["function_params", "query", "raw_data", "aggrid_data", "chart_info", 
                     "conversational_analytics", "data_source", "response_type"]
    
    for key in required_keys:
        assert key in tech_details, f"❌ Chave '{key}' não encontrada em tech_details"
    
    print(f"   ✅ Todas as chaves obrigatórias presentes:")
    for key in required_keys:
        print(f"      - {key}: ✓")
    
    # Teste 7: Chart Figure Validation
    print("\n7️⃣  Validando figura do gráfico...")
    if tech_details["chart_info"] and tech_details["chart_info"].get("fig"):
        fig_dict = tech_details["chart_info"]["fig"]
        assert isinstance(fig_dict, dict), "❌ Figure não é dicionário"
        assert "data" in fig_dict, "❌ 'data' não encontrado em figure"
        assert "layout" in fig_dict, "❌ 'layout' não encontrado em figure"
        print(f"   ✅ Figura validada com sucesso")
        print(f"      - Estrutura: {'data' in fig_dict and 'layout' in fig_dict}")
        print(f"      - Tipo gráfico: {tech_details['chart_info'].get('type')}")
    
    print("\n" + "=" * 70)
    print("✅ TODAS AS VALIDAÇÕES PASSARAM COM SUCESSO!")
    print("=" * 70)
    print("\n📊 Resumo:")
    print(f"   • Detecção de fonte: OK")
    print(f"   • Extração de parâmetros: OK")
    print(f"   • Processamento de Natura: OK")
    print(f"   • Geração de figura: OK")
    print(f"   • Estrutura de tech_details: OK")
    print(f"   • Integração completa: OK")
    
    return True

if __name__ == "__main__":
    try:
        success = validate_ca_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
