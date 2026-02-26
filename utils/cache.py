import duckdb
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Definir DB_PATH relativo ao diretório do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "cache.db")

def get_connection():
    """Retorna conexão com o DuckDB"""
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
    
    # Serialização segura para evitar erros do DuckDB
    def safe_json_dumps(obj):
        if obj is None:
            return None
        try:
            return json.dumps(obj)
        except (TypeError, ValueError) as e:
            print(f"AVISO: Erro ao serializar {type(obj)}: {e}. Convertendo para string.")
            return json.dumps({"serialized_as_string": str(obj)})
    
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
            safe_json_dumps(function_params),
            query_sql,
            safe_json_dumps(raw_data),
            raw_response,
            refined_response,
            safe_json_dumps(tech_details),
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
    """Recupera o histórico do usuário com amostra dos dados para eficiência"""
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
            # Otimização: para o histórico, inclui apenas amostra dos dados (primeiras 5 linhas)
            raw_data = json.loads(row[5]) if row[5] else None
            sample_data = raw_data[:5] if raw_data and isinstance(raw_data, list) else raw_data
            
            history.append({
                'id': row[0],
                'timestamp': row[1],
                'question': row[2],
                'user_prompt': row[2],  # Adiciona o campo user_prompt para compatibilidade
                'function_params': json.loads(row[3]) if row[3] else None,
                'query_sql': row[4],
                'raw_data_sample': sample_data,  # Apenas amostra para análise
                'raw_data_count': len(raw_data) if raw_data and isinstance(raw_data, list) else 0,
                'refined_response': row[6],
                'tech_details': json.loads(row[7]) if row[7] else None,
                'reused_from': row[8]
            })
        
        return history

def get_interaction_full_data(interaction_id: str) -> Optional[List]:
    """Recupera os dados completos de uma interação específica"""
    with get_connection() as conn:
        result = conn.execute("""
            SELECT raw_data FROM user_interactions 
            WHERE id = ? AND status = 'OK'
        """, (interaction_id,)).fetchone()
        
        if result and result[0]:
            return json.loads(result[0])
        return None

def get_most_recent_data_interaction(user_id: str) -> Optional[Dict]:
    """Recupera a interação mais recente que retornou dados (para casos como 'gere um gráfico desse dado')"""
    with get_connection() as conn:
        result = conn.execute("""
            SELECT id, timestamp, question, function_params, query_sql, raw_data, 
                   refined_response, tech_details
            FROM user_interactions 
            WHERE user_id = ? AND status = 'OK' AND raw_data IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (user_id,)).fetchone()
        
        if result:
            return {
                'id': result[0],
                'timestamp': result[1],
                'question': result[2],
                'function_params': json.loads(result[3]) if result[3] else None,
                'query_sql': result[4],
                'raw_data': json.loads(result[5]) if result[5] else None,
                'refined_response': result[6],
                'tech_details': json.loads(result[7]) if result[7] else None
            }
    
    return None

def find_reusable(user_id: str, question: str) -> Optional[Dict]:
    """Busca interações que podem ser reutilizadas - OTIMIZADO para priorizar dados recentes"""
    # Palavras-chave que indicam reutilização EXPLÍCITA de dados específicos
    explicit_recent_keywords = [
        "gráfico", "grafico", "chart", "exportar", "excel", "planilha", "csv",
        "visualização", "visualizacao", "plotar", "plot"
    ]
    
    # Palavras-chave que indicam reutilização de dados ANTERIORES específicos
    specific_reference_keywords = [
        "mesmos dados", "dados anteriores", "última consulta", "último resultado", 
        "tabela anterior", "consulta anterior", "resultado anterior"
    ]
    
    question_lower = question.lower()
    
    # CASO 1: Referência explícita a dados anteriores específicos
    has_specific_reference = any(keyword in question_lower for keyword in specific_reference_keywords)
    
    # CASO 2: Pedido de visualização/export (implica usar dados mais recentes)
    has_visualization_request = any(keyword in question_lower for keyword in explicit_recent_keywords)
    
    # CASO 3: Frases que indicam continuidade ("agora", "desse", "destes dados")
    continuity_keywords = ["agora", "desse", "destes", "dessa", "dessas", "do resultado", "dos dados"]
    has_continuity = any(keyword in question_lower for keyword in continuity_keywords)
    
    # Se não há indicadores de reutilização, retorna None
    if not (has_specific_reference or has_visualization_request or has_continuity):
        return None
    
    with get_connection() as conn:
        # PRIORIDADE: Se é pedido de visualização/export OU tem continuidade, usa dados mais recentes
        if (has_visualization_request or has_continuity) and not has_specific_reference:
            # Busca a última interação bem-sucedida com dados (mais recente)
            result = conn.execute("""
                SELECT id, question, function_params, query_sql, raw_data, 
                       refined_response, tech_details, timestamp
                FROM user_interactions 
                WHERE user_id = ? AND status = 'OK' AND raw_data IS NOT NULL
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (user_id,)).fetchone()
        else:
            # Para referências específicas a dados anteriores, mantém lógica original
            result = conn.execute("""
                SELECT id, question, function_params, query_sql, raw_data, 
                       refined_response, tech_details, timestamp
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
                'tech_details': json.loads(result[6]) if result[6] else None,
                'timestamp': result[7],
                'reuse_reason': 'most_recent_data' if (has_visualization_request or has_continuity) else 'specific_reference'
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
    
    try:
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
    except Exception as e:
        # Se falhar por tabela inexistente, tenta criar e repetir
        if "log_erros" in str(e) and ("does not exist" in str(e) or "no such table" in str(e)):
            try:
                with get_connection() as conn:
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
            except Exception as e2:
                print(f"[log_error][FATAL] Falha ao criar tabela log_erros e registrar erro: {e2}")
                return None
        else:
            print(f"[log_error][FATAL] Falha ao registrar erro: {e}")
            return None

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
try:
    init_cache_db()
    print(f"[Cache] ✅ Banco inicializado: {DB_PATH}")
except Exception as e:
    print(f"[Cache] ⚠️  Erro ao inicializar banco: {e}")
    raise
