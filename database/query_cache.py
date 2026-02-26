import duckdb
import json
import os
from datetime import datetime

# test_rag.py
from rag_system.business_metadata_rag import BusinessMetadataRAGV2

# Definir caminho do cache DB relativo ao projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DB_PATH = os.path.join(PROJECT_ROOT, "cache.db")

def test_rag_system():
    rag = BusinessMetadataRAGV2()
    
    print("=== TESTE DE CARREGAMENTO ===")
    metadata_list = rag.extract_table_metadata()
    print(f"Tabelas carregadas: {len(metadata_list)}")
    for metadata in metadata_list:
        print(f"- {metadata.table_name}: {metadata.domain}")
    
    print("\n=== TESTE DE CONSULTAS ===")
    test_queries = [
        "vendas de veículos",
        "contratos de consórcio ativos", 
        "histórico de vendas de cotas",
        "dados financeiros e orçamento"
    ]
    
    for query in test_queries:
        print(f"\n--- Consulta: '{query}' ---")
        contexts = rag.retrieve_relevant_context(query, similarity_threshold=0.3)
        if contexts:
            for context in contexts:
                table_name = context.split('===')[1].strip()
                print(f"Tabela relevante: {table_name}")
        else:
            print("Nenhum contexto relevante encontrado")


def query_cache():
    """Executa consultas úteis no cache DuckDB"""
    
    try:
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
        conn = duckdb.connect(CACHE_DB_PATH)
        
        print("=" * 60)
        print("🔍 CONSULTA DO CACHE DUCKDB")
        print("=" * 60)
        
        # 1. Tabelas disponíveis
        print("\n📋 TABELAS DISPONÍVEIS:")
        tables = conn.execute("SHOW TABLES").fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # 2. Estatísticas gerais
        print("\n📊 ESTATÍSTICAS GERAIS:")
        
        total_interactions = conn.execute("SELECT COUNT(*) FROM user_interactions").fetchone()[0]
        print(f"  Total de interações: {total_interactions}")
        
        total_users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_interactions").fetchone()[0]
        print(f"  Total de usuários: {total_users}")
        
        reused_count = conn.execute("SELECT COUNT(*) FROM user_interactions WHERE reused_from IS NOT NULL").fetchone()[0]
        print(f"  Interações reutilizadas: {reused_count}")
        
        error_count = conn.execute("SELECT COUNT(*) FROM log_erros").fetchone()[0]
        print(f"  Total de erros: {error_count}")
        
        # 3. Interações por usuário
        print("\n👥 INTERAÇÕES POR USUÁRIO:")
        user_stats = conn.execute("""
            SELECT user_id, 
                   COUNT(*) as total,
                   SUM(CASE WHEN reused_from IS NOT NULL THEN 1 ELSE 0 END) as reused,
                   MAX(timestamp) as last_activity
            FROM user_interactions 
            GROUP BY user_id
            ORDER BY total DESC
        """).fetchall()
        
        for user, total, reused, last_activity in user_stats:
            print(f"  {user}: {total} total, {reused} reutilizadas, última: {last_activity}")
        
        # 4. Interações mais recentes
        print("\n⏰ INTERAÇÕES MAIS RECENTES (10):")
        recent = conn.execute("""
            SELECT timestamp, user_id, question, status,
                   CASE WHEN reused_from IS NOT NULL THEN 'REUTILIZADA' ELSE 'NOVA' END as tipo
            FROM user_interactions 
            ORDER BY timestamp DESC 
            LIMIT 10
        """).fetchall()
        
        for timestamp, user, question, status, tipo in recent:
            question_short = question[:50] + "..." if len(question) > 50 else question
            print(f"  [{timestamp}] {user} ({tipo}): {question_short}")
        
        # 5. Análise completa de erros
        print("\n" + "="*80)
        print("🔥 ANÁLISE COMPLETA DE ERROS")
        print("="*80)
        
        # 5.1 Estatísticas de erro por tipo
        print("\n📊 ERROS POR TIPO:")
        error_types = conn.execute("""
            SELECT error_type, 
                   COUNT(*) as total,
                   COUNT(DISTINCT user_id) as usuarios_afetados,
                   MIN(timestamp) as primeiro_erro,
                   MAX(timestamp) as ultimo_erro
            FROM log_erros 
            GROUP BY error_type
            ORDER BY total DESC
        """).fetchall()
        
        for error_type, total, users, first, last in error_types:
            print(f"\n  🔴 {error_type}")
            print(f"     Total: {total} erros")
            print(f"     Usuários afetados: {users}")
            print(f"     Período: {first} até {last}")
        
        # 5.2 Todos os erros com detalhes completos
        print(f"\n" + "="*80)
        print("📋 TODOS OS ERROS REGISTRADOS (DETALHADOS)")
        print("="*80)
        
        all_errors = conn.execute("""
            SELECT timestamp, user_id, error_type, error_message, context, traceback
            FROM log_erros 
            ORDER BY timestamp DESC
        """).fetchall()
        
        if all_errors:
            for i, (timestamp, user, error_type, error_msg, context, traceback) in enumerate(all_errors, 1):
                print(f"\n{'='*60}")
                print(f"ERRO #{i} - {error_type}")
                print(f"{'='*60}")
                print(f"⏰ Timestamp: {timestamp}")
                print(f"👤 Usuário: {user}")
                print(f"🔴 Tipo: {error_type}")
                
                print(f"\n📝 MENSAGEM DE ERRO:")
                print("-" * 40)
                # Formata a mensagem de erro com quebras de linha para legibilidade
                error_lines = error_msg.split('\\n') if '\\n' in error_msg else [error_msg]
                for line in error_lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                
                if context:
                    print(f"\n🔍 CONTEXTO:")
                    print("-" * 40)
                    # Tenta fazer parse do contexto se for JSON
                    try:
                        if context.startswith('{') or context.startswith('['):
                            import json
                            context_dict = json.loads(context)
                            for key, value in context_dict.items():
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"   {key}: {value[:100]}...")
                                else:
                                    print(f"   {key}: {value}")
                        else:
                            # Contexto simples - quebra em linhas se muito longo
                            context_lines = context.split('|') if '|' in context else [context]
                            for line in context_lines:
                                if line.strip():
                                    print(f"   {line.strip()}")
                    except:
                        # Se falhar o parse, mostra o contexto bruto mas formatado
                        if len(context) > 200:
                            print(f"   {context[:200]}...")
                            print(f"   ... (contexto truncado, total: {len(context)} chars)")
                        else:
                            print(f"   {context}")
                
                if traceback:
                    print(f"\n🐛 TRACEBACK:")
                    print("-" * 40)
                    # Formata o traceback com indentação
                    traceback_lines = traceback.split('\\n') if '\\n' in traceback else traceback.split('\n')
                    for line in traceback_lines:
                        if line.strip():
                            # Destaca linhas importantes do traceback
                            if 'File "' in line and '.py' in line:
                                print(f"   📁 {line.strip()}")
                            elif 'Error:' in line or 'Exception:' in line:
                                print(f"   ⚠️  {line.strip()}")
                            else:
                                print(f"      {line.strip()}")
                
                print("\n" + "="*60)
        else:
            print("   ✅ Nenhum erro registrado!")
        
        # 5.3 Padrões de erro mais comuns
        print(f"\n" + "="*80)
        print("🔍 ANÁLISE DE PADRÕES DE ERRO")
        print("="*80)
        
        # Erros por palavra-chave na mensagem
        print("\n📊 PALAVRAS-CHAVE MAIS COMUNS NOS ERROS:")
        keywords_query = conn.execute("""
            SELECT 
                SUM(CASE WHEN error_message LIKE '%finish_reason%' THEN 1 ELSE 0 END) as finish_reason_errors,
                SUM(CASE WHEN error_message LIKE '%safety%' THEN 1 ELSE 0 END) as safety_errors,
                SUM(CASE WHEN error_message LIKE '%timeout%' THEN 1 ELSE 0 END) as timeout_errors,
                SUM(CASE WHEN error_message LIKE '%connection%' THEN 1 ELSE 0 END) as connection_errors,
                SUM(CASE WHEN error_message LIKE '%missing%' THEN 1 ELSE 0 END) as missing_errors,
                SUM(CASE WHEN error_message LIKE '%SQL%' OR error_message LIKE '%sql%' THEN 1 ELSE 0 END) as sql_errors,
                SUM(CASE WHEN error_message LIKE '%JSON%' OR error_message LIKE '%json%' THEN 1 ELSE 0 END) as json_errors
            FROM log_erros
        """).fetchone()
        
        if keywords_query:
            finish_reason, safety, timeout, connection, missing, sql, json_errs = keywords_query
            if finish_reason > 0: print(f"   🚫 finish_reason: {finish_reason} erros")
            if safety > 0: print(f"   🛡️ safety: {safety} erros")
            if timeout > 0: print(f"   ⏱️ timeout: {timeout} erros")
            if connection > 0: print(f"   🔌 connection: {connection} erros")
            if missing > 0: print(f"   ❓ missing: {missing} erros")
            if sql > 0: print(f"   🗄️ SQL: {sql} erros")
            if json_errs > 0: print(f"   📋 JSON: {json_errs} erros")
        
        # Erros por horário (para identificar padrões temporais)
        print("\n⏰ DISTRIBUIÇÃO DE ERROS POR HORA:")
        hourly_errors = conn.execute("""
            SELECT strftime('%H', timestamp) as hora, COUNT(*) as total
            FROM log_erros 
            GROUP BY strftime('%H', timestamp)
            ORDER BY hora
        """).fetchall()
        
        for hora, total in hourly_errors:
            bar = "█" * min(total, 20)  # Gráfico simples em ASCII
            print(f"   {hora}h: {bar} ({total})")
        
        print(f"\n" + "="*80)
        
        # 6. Análise de interações com problema
        print("🔄 INTERAÇÕES QUE GERARAM ERROS:")
        problematic_interactions = conn.execute("""
            SELECT ui.timestamp, ui.user_id, ui.question, ui.status,
                   le.error_type, le.error_message
            FROM user_interactions ui
            LEFT JOIN log_erros le ON ui.user_id = le.user_id 
                AND abs(epoch(ui.timestamp::timestamp) - epoch(le.timestamp::timestamp)) <= 60
            WHERE le.error_message IS NOT NULL
            ORDER BY ui.timestamp DESC
        """).fetchall()
        
        if problematic_interactions:
            for timestamp, user, question, status, error_type, error_msg in problematic_interactions:
                question_short = question[:80] + "..." if len(question) > 80 else question
                error_short = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                print(f"\n   📅 {timestamp}")
                print(f"   👤 Usuário: {user}")
                print(f"   ❓ Pergunta: {question_short}")
                print(f"   📊 Status: {status}")
                print(f"   ❌ Erro: {error_type} - {error_short}")
                print(f"   {'-'*60}")
        else:
            print("   ✅ Nenhuma interação com erro identificada!")
        
        # 7. Dados de uma interação específica (exemplo mais detalhado)
        print("\n" + "="*80)
        print("🔎 EXEMPLO DE DADOS COMPLETOS (ÚLTIMA INTERAÇÃO)")
        print("="*80)
        sample = conn.execute("""
            SELECT question, function_params, query_sql, tech_details, raw_data, status
            FROM user_interactions 
            WHERE raw_data IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 1
        """).fetchone()
        
        if sample:
            question, params, query, tech, raw_data, status = sample
            print(f"\n📝 PERGUNTA:")
            print(f"   {question}")
            
            print(f"\n📊 STATUS: {status}")
            
            if params:
                print(f"\n⚙️ PARÂMETROS DA FUNÇÃO:")
                try:
                    params_dict = json.loads(params)
                    for key, value in params_dict.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"   {key}: {value[:100]}...")
                        else:
                            print(f"   {key}: {value}")
                except:
                    print(f"   {params}")
            
            if query:
                print(f"\n🗄️ QUERY SQL GERADA:")
                # Formata a query SQL com indentação
                query_lines = query.replace('\\n', '\n').split('\n')
                for line in query_lines:
                    if line.strip():
                        print(f"   {line}")
            
            if tech:
                print(f"\n🔧 DETALHES TÉCNICOS:")
                try:
                    if tech.startswith('{') or tech.startswith('['):
                        tech_dict = json.loads(tech)
                        for key, value in tech_dict.items():
                            if isinstance(value, str) and len(value) > 150:
                                print(f"   {key}: {value[:150]}...")
                            else:
                                print(f"   {key}: {value}")
                    else:
                        print(f"   {tech}")
                except:
                    print(f"   {tech}")
            
            if raw_data:
                print(f"\n📋 DADOS BRUTOS (PRIMEIROS 500 CHARS):")
                raw_preview = raw_data[:500] + "..." if len(raw_data) > 500 else raw_data
                print(f"   {raw_preview}")
                print(f"   Total de dados: {len(raw_data)} caracteres")
        
        # 8. Resumo executivo
        print("\n" + "="*80)
        print("📈 RESUMO EXECUTIVO DO DEBUG")
        print("="*80)
        
        # Calcular métricas importantes
        total_interactions = conn.execute("SELECT COUNT(*) FROM user_interactions").fetchone()[0]
        total_errors = conn.execute("SELECT COUNT(*) FROM log_erros").fetchone()[0]
        error_rate = (total_errors / total_interactions * 100) if total_interactions > 0 else 0
        
        unique_error_types = conn.execute("SELECT COUNT(DISTINCT error_type) FROM log_erros").fetchone()[0]
        users_with_errors = conn.execute("SELECT COUNT(DISTINCT user_id) FROM log_erros").fetchone()[0]
        
        print(f"\n📊 MÉTRICAS GERAIS:")
        print(f"   Total de interações: {total_interactions}")
        print(f"   Total de erros: {total_errors}")
        print(f"   Taxa de erro: {error_rate:.2f}%")
        print(f"   Tipos únicos de erro: {unique_error_types}")
        print(f"   Usuários com erros: {users_with_errors}")
        
        # Tipo de erro mais comum
        most_common_error = conn.execute("""
            SELECT error_type, COUNT(*) as count
            FROM log_erros 
            GROUP BY error_type 
            ORDER BY count DESC 
            LIMIT 1
        """).fetchone()
        
        if most_common_error:
            print(f"\n🔥 PROBLEMA MAIS CRÍTICO:")
            print(f"   Tipo: {most_common_error[0]}")
            print(f"   Ocorrências: {most_common_error[1]}")
            
            # Pegar um exemplo deste erro mais comum
            example_error = conn.execute("""
                SELECT error_message, context 
                FROM log_erros 
                WHERE error_type = ?
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (most_common_error[0],)).fetchone()
            
            if example_error:
                print(f"   Exemplo: {example_error[0][:100]}...")
        
        # Período com mais erros
        busiest_day = conn.execute("""
            SELECT date(timestamp) as dia, COUNT(*) as erros
            FROM log_erros 
            GROUP BY date(timestamp)
            ORDER BY erros DESC 
            LIMIT 1
        """).fetchone()
        
        if busiest_day:
            print(f"\n📅 DIA COM MAIS ERROS:")
            print(f"   Data: {busiest_day[0]}")
            print(f"   Erros: {busiest_day[1]}")
        
        # Recomendações baseadas nos dados
        print(f"\n💡 RECOMENDAÇÕES PARA DEBUG:")
        
        if error_rate > 10:
            print("   🚨 ALTA taxa de erro detectada - investigar causas raiz urgentemente")
        elif error_rate > 5:
            print("   ⚠️ Taxa de erro moderada - monitorar e otimizar")
        else:
            print("   ✅ Taxa de erro baixa - sistema estável")
        
        # Verificar padrões específicos
        safety_errors = conn.execute("SELECT COUNT(*) FROM log_erros WHERE error_message LIKE '%safety%' OR error_message LIKE '%finish_reason%'").fetchone()[0]
        if safety_errors > 0:
            print(f"   🛡️ {safety_errors} erros de segurança/bloqueio - revisar prompts e filtros")
        
        sql_errors = conn.execute("SELECT COUNT(*) FROM log_erros WHERE error_message LIKE '%SQL%' OR error_message LIKE '%sql%'").fetchone()[0]
        if sql_errors > 0:
            print(f"   🗄️ {sql_errors} erros SQL - verificar geração de queries")
        
        json_errors = conn.execute("SELECT COUNT(*) FROM log_erros WHERE error_message LIKE '%JSON%' OR error_message LIKE '%json%'").fetchone()[0]
        if json_errors > 0:
            print(f"   📋 {json_errors} erros JSON - verificar parsing de dados")
        
        connection_errors = conn.execute("SELECT COUNT(*) FROM log_erros WHERE error_message LIKE '%connection%' OR error_message LIKE '%timeout%'").fetchone()[0]
        if connection_errors > 0:
            print(f"   🔌 {connection_errors} erros de conexão - verificar conectividade")
        
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ RELATÓRIO DE DEBUG COMPLETO!")
        print("="*80)
        print("📋 Use este relatório para:")
        print("   • Identificar padrões de erro")
        print("   • Priorizar correções")
        print("   • Monitorar estabilidade do modelo")
        print("   • Melhorar prompts e validações")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Erro ao consultar cache: {e}")
        import traceback
        print("🐛 Detalhes do erro:")
        traceback.print_exc()
    
if __name__ == "__main__":
    query_cache()