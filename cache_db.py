import duckdb
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

DB_PATH = "cache.db"

def get_connection():
    """Retorna conexão com o DuckDB"""
    return duckdb.connect(DB_PATH)

def init_cache_db():
    """Inicializa as tabelas do cache"""
    with get_connection() as conn:
        # Tabela de interações do usuário
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                question TEXT NOT NULL,
                function_params TEXT,
                query_sql TEXT,
                raw_data TEXT,
                raw_response TEXT,
                refined_response TEXT,
                tech_details TEXT,
                status VARCHAR DEFAULT 'OK',
                reused_from VARCHAR
            )
        """)
        
        # Tabela de erros
        conn.execute("""
            CREATE TABLE IF NOT EXISTS log_erros (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_type VARCHAR,
                error_message TEXT,
                context TEXT,
                traceback TEXT
            )
        """)

def save_interaction(
    user_id: str,
    question: str,
    function_params: Optional[Dict] = None,
    query_sql: Optional[str] = None,
    raw_data: Optional[List] = None,
    raw_response: Optional[str] = None,
    refined_response: Optional[str] = None,
    tech_details: Optional[Dict] = None,
    status: str = "OK",
    reused_from: Optional[str] = None
) -> str:
    """Salva uma interação no cache"""
    interaction_id = str(uuid.uuid4())
    
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO user_interactions 
            (id, user_id, question, function_params, query_sql, raw_data, 
             raw_response, refined_response, tech_details, status, reused_from)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction_id,
            user_id,
            question,
            json.dumps(function_params) if function_params else None,
            query_sql,
            json.dumps(raw_data) if raw_data else None,
            raw_response,
            refined_response,
            json.dumps(tech_details) if tech_details else None,
            status,
            reused_from
        ))
        
        # Limita a 15 interações por usuário
        conn.execute("""
            DELETE FROM user_interactions 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM user_interactions 
                WHERE user_id = ? AND status = 'OK'
                ORDER BY timestamp DESC 
                LIMIT 15
            )
        """, (user_id, user_id))
    
    return interaction_id

def get_user_history(user_id: str, limit: int = 15) -> List[Dict]:
    """Recupera o histórico do usuário"""
    with get_connection() as conn:
        result = conn.execute("""
            SELECT id, timestamp, question, function_params, query_sql, 
                   raw_data, refined_response, tech_details, reused_from
            FROM user_interactions 
            WHERE user_id = ? AND status = 'OK'
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit)).fetchall()
        
        history = []
        for row in result:
            history.append({
                'id': row[0],
                'timestamp': row[1],
                'question': row[2],
                'user_prompt': row[2],  # Adiciona o campo user_prompt para compatibilidade
                'function_params': json.loads(row[3]) if row[3] else None,
                'query_sql': row[4],
                'raw_data': json.loads(row[5]) if row[5] else None,
                'refined_response': row[6],
                'tech_details': json.loads(row[7]) if row[7] else None,
                'reused_from': row[8]
            })
        
        return history

def find_reusable(user_id: str, question: str) -> Optional[Dict]:
    """Busca interações que podem ser reutilizadas"""
    # Palavras-chave que indicam reutilização
    reuse_keywords = [
        "gráfico", "excel", "exportar", "mesmos dados", "dados anteriores",
        "última consulta", "último resultado", "tabela anterior"
    ]
    
    question_lower = question.lower()
    
    # Verifica se a pergunta contém palavras de reutilização
    if not any(keyword in question_lower for keyword in reuse_keywords):
        return None
    
    with get_connection() as conn:
        # Busca a última interação bem-sucedida com dados
        result = conn.execute("""
            SELECT id, question, function_params, query_sql, raw_data, 
                   refined_response, tech_details
            FROM user_interactions 
            WHERE user_id = ? AND status = 'OK' AND raw_data IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (user_id,)).fetchone()
        
        if result:
            return {
                'id': result[0],
                'question': result[1],
                'function_params': json.loads(result[2]) if result[2] else None,
                'query_sql': result[3],
                'raw_data': json.loads(result[4]) if result[4] else None,
                'refined_response': result[5],
                'tech_details': json.loads(result[6]) if result[6] else None
            }
    
    return None

def get_context_for_question(user_id: str, question: str) -> str:
    """Gera contexto baseado no histórico para melhorar a pergunta"""
    history = get_user_history(user_id, 5)  # Últimas 5 interações
    
    if not history:
        return ""
    
    context_parts = ["Histórico recente do usuário:"]
    
    for i, interaction in enumerate(history, 1):
        context_parts.append(f"{i}. Pergunta: {interaction['question']}")
        if interaction['reused_from']:
            context_parts.append(f"   (Reutilizou dados de interação anterior)")
    
    return "\n".join(context_parts)

def log_error(
    user_id: str,
    error_type: str,
    error_message: str,
    context: Optional[str] = None,
    traceback: Optional[str] = None
) -> str:
    """Registra um erro no banco de dados"""
    error_id = str(uuid.uuid4())
    
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO log_erros 
            (id, user_id, error_type, error_message, context, traceback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            error_id,
            user_id,
            error_type,
            error_message,
            context,
            traceback
        ))
    
    return error_id

def get_recent_errors(user_id: str, hours: int = 24) -> List[Dict]:
    """Recupera erros recentes do usuário"""
    with get_connection() as conn:
        result = conn.execute("""
            SELECT id, timestamp, error_type, error_message, context
            FROM log_erros 
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (user_id, datetime.now() - timedelta(hours=hours))).fetchall()
        
        errors = []
        for row in result:
            errors.append({
                'id': row[0],
                'timestamp': row[1],
                'error_type': row[2],
                'error_message': row[3],
                'context': row[4]
            })
        
        return errors

# Inicializa o banco ao importar o módulo
init_cache_db()
