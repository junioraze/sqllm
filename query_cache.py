#!/usr/bin/env python3
"""
Script para consultar o cache DuckDB
Uso: python query_cache.py
"""

import duckdb
import json
from datetime import datetime

def query_cache():
    """Executa consultas úteis no cache DuckDB"""
    
    try:
        conn = duckdb.connect('cache.db')
        
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
        
        # 5. Erros recentes
        print("\n❌ ERROS RECENTES (5):")
        errors = conn.execute("""
            SELECT timestamp, user_id, error_type, error_message
            FROM log_erros 
            ORDER BY timestamp DESC 
            LIMIT 5
        """).fetchall()
        
        if errors:
            for timestamp, user, error_type, error_msg in errors:
                error_short = error_msg[:2000] + "..." if len(error_msg) > 2000 else error_msg
                print(f"  [{timestamp}] {user} - {error_type}: {error_short}")
        else:
            print("  Nenhum erro registrado!")
        
        # 6. Dados de uma interação específica (exemplo)
        print("\n🔎 EXEMPLO DE DADOS COMPLETOS:")
        sample = conn.execute("""
            SELECT question, function_params, query_sql, tech_details
            FROM user_interactions 
            WHERE raw_data IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 1
        """).fetchone()
        
        if sample:
            question, params, query, tech = sample
            print(f"  Pergunta: {question}")
            print(f"  Query SQL: {query}")
            if params:
                try:
                    params_dict = json.loads(params)
                    print(f"  Parâmetros: {params_dict}")
                except:
                    print(f"  Parâmetros: {params}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Consulta concluída!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao consultar cache: {e}")

if __name__ == "__main__":
    query_cache()
