"""
Sistema de Métricas e Monitoramento de IA
=========================================

Tracking completo de custos, performance e qualidade para otimização contínua
do sistema de IA. Inclui métricas de token usage, tempo de resposta, 
precisão de queries e satisfação do usuário.
"""
import json
import time
import duckdb
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

class MetricType(Enum):
    TOKEN_USAGE = "token_usage"
    RESPONSE_TIME = "response_time"
    QUERY_ACCURACY = "query_accuracy"
    USER_SATISFACTION = "user_satisfaction"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    COST_TRACKING = "cost_tracking"

@dataclass
class AIMetric:
    """Métrica individual do sistema de IA"""
    id: str
    metric_type: MetricType
    timestamp: datetime
    user_id: str
    session_id: str
    value: float
    unit: str
    context: Dict[str, Any]
    tags: Dict[str, str]

@dataclass
class TokenUsageMetric:
    """Métricas específicas de uso de tokens"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model_name: str
    prompt_type: str
    optimization_applied: bool

@dataclass
class PerformanceMetric:
    """Métricas de performance do sistema"""
    total_duration_ms: float
    rag_retrieval_ms: float
    prompt_generation_ms: float
    llm_inference_ms: float
    post_processing_ms: float
    cache_lookup_ms: float

@dataclass
class QualityMetric:
    """Métricas de qualidade das respostas"""
    query_success: bool
    result_count: int
    user_feedback: Optional[int] = None  # 1-5 rating
    query_complexity_score: float = 0.0
    metadata_relevance_score: float = 0.0
    prompt_efficiency_score: float = 0.0

class AIMetricsCollector:
    """Coletor central de métricas do sistema de IA"""
    
    def __init__(self, db_path: str = "ai_metrics.db"):
        self.db_path = db_path
        self.session_cache = {}
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de métricas"""
        with duckdb.connect(self.db_path) as conn:
            # Tabela principal de métricas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_metrics (
                    id VARCHAR PRIMARY KEY,
                    metric_type VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    user_id VARCHAR NOT NULL,
                    session_id VARCHAR NOT NULL,
                    value DOUBLE NOT NULL,
                    unit VARCHAR NOT NULL,
                    context_json TEXT,
                    tags_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de sessões de usuário  
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP,
                    total_queries INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd DOUBLE DEFAULT 0.0,
                    avg_response_time_ms DOUBLE DEFAULT 0.0,
                    success_rate DOUBLE DEFAULT 1.0
                )
            """)
            
            # Tabela de custos diários agregados
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_cost_summary (
                    date DATE PRIMARY KEY,
                    total_queries INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd DOUBLE DEFAULT 0.0,
                    avg_tokens_per_query DOUBLE DEFAULT 0.0,
                    unique_users INTEGER DEFAULT 0,
                    cache_hit_rate DOUBLE DEFAULT 0.0
                )
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON ai_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_user ON ai_metrics(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON ai_metrics(metric_type)")
    
    def start_session(self, user_id: str) -> str:
        """Inicia uma nova sessão de usuário"""
        session_id = str(uuid.uuid4())
        
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_sessions (session_id, user_id, started_at)
                VALUES (?, ?, ?)
            """, (session_id, user_id, datetime.now()))
        
        self.session_cache[session_id] = {
            "user_id": user_id,
            "start_time": time.time(),
            "queries": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
        
        return session_id
    
    def record_token_usage(
        self,
        session_id: str,
        user_id: str,
        usage: TokenUsageMetric,
        context: Dict[str, Any] = None
    ):
        """Registra uso de tokens"""
        metric = AIMetric(
            id=str(uuid.uuid4()),
            metric_type=MetricType.TOKEN_USAGE,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            value=usage.total_tokens,
            unit="tokens",
            context={
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "estimated_cost": usage.estimated_cost_usd,
                "model": usage.model_name,
                "prompt_type": usage.prompt_type,
                "optimization_applied": usage.optimization_applied,
                **( context or {})
            },
            tags={
                "model": usage.model_name,
                "optimization": str(usage.optimization_applied)
            }
        )
        
        self._save_metric(metric)
        
        # Atualiza cache da sessão
        if session_id in self.session_cache:
            self.session_cache[session_id]["total_tokens"] += usage.total_tokens
            self.session_cache[session_id]["total_cost"] += usage.estimated_cost_usd
    
    def record_performance(
        self,
        session_id: str,
        user_id: str,
        performance: PerformanceMetric,
        context: Dict[str, Any] = None
    ):
        """Registra métricas de performance"""
        metric = AIMetric(
            id=str(uuid.uuid4()),
            metric_type=MetricType.RESPONSE_TIME,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            value=performance.total_duration_ms,
            unit="milliseconds",
            context={
                "rag_retrieval_ms": performance.rag_retrieval_ms,
                "prompt_generation_ms": performance.prompt_generation_ms,
                "llm_inference_ms": performance.llm_inference_ms,
                "post_processing_ms": performance.post_processing_ms,
                "cache_lookup_ms": performance.cache_lookup_ms,
                **(context or {})
            },
            tags={
                "performance_tier": self._classify_performance(performance.total_duration_ms)
            }
        )
        
        self._save_metric(metric)
    
    def record_quality(
        self,
        session_id: str,
        user_id: str,
        quality: QualityMetric,
        context: Dict[str, Any] = None
    ):
        """Registra métricas de qualidade"""
        metric = AIMetric(
            id=str(uuid.uuid4()),
            metric_type=MetricType.QUERY_ACCURACY,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            value=1.0 if quality.query_success else 0.0,
            unit="success_rate",
            context={
                "result_count": quality.result_count,
                "user_feedback": quality.user_feedback,
                "complexity_score": quality.query_complexity_score,
                "metadata_relevance": quality.metadata_relevance_score,
                "prompt_efficiency": quality.prompt_efficiency_score,
                **(context or {})
            },
            tags={
                "success": str(quality.query_success),
                "complexity": self._classify_complexity(quality.query_complexity_score)
            }
        )
        
        self._save_metric(metric)
        
        # Atualiza contadores de sessão
        if session_id in self.session_cache:
            self.session_cache[session_id]["queries"] += 1
    
    def record_cache_hit(
        self,
        session_id: str,
        user_id: str,
        hit: bool,
        cache_type: str,
        context: Dict[str, Any] = None
    ):
        """Registra hit/miss de cache"""
        metric = AIMetric(
            id=str(uuid.uuid4()),
            metric_type=MetricType.CACHE_HIT_RATE,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            value=1.0 if hit else 0.0,
            unit="hit_rate",
            context={
                "cache_type": cache_type,
                **(context or {})
            },
            tags={
                "cache_type": cache_type,
                "hit": str(hit)
            }
        )
        
        self._save_metric(metric)
    
    def record_cost(
        self,
        session_id: str,
        user_id: str,
        cost_usd: float,
        cost_type: str,
        context: Dict[str, Any] = None
    ):
        """Registra custos do sistema"""
        metric = AIMetric(
            id=str(uuid.uuid4()),
            metric_type=MetricType.COST_TRACKING,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            value=cost_usd,
            unit="usd",
            context={
                "cost_type": cost_type,
                **(context or {})
            },
            tags={
                "cost_type": cost_type
            }
        )
        
        self._save_metric(metric)
    
    def end_session(self, session_id: str):
        """Finaliza uma sessão de usuário"""
        if session_id not in self.session_cache:
            return
        
        session_data = self.session_cache[session_id]
        duration = time.time() - session_data["start_time"]
        
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE user_sessions 
                SET 
                    ended_at = ?,
                    total_queries = ?,
                    total_tokens = ?,
                    total_cost_usd = ?,
                    avg_response_time_ms = ?
                WHERE session_id = ?
            """, (
                datetime.now(),
                session_data["queries"],
                session_data["total_tokens"],
                session_data["total_cost"],
                duration * 1000 / max(session_data["queries"], 1),
                session_id
            ))
        
        del self.session_cache[session_id]
    
    def _save_metric(self, metric: AIMetric):
        """Salva métrica no banco de dados"""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_metrics 
                (id, metric_type, timestamp, user_id, session_id, value, unit, context_json, tags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.id,
                metric.metric_type.value,
                metric.timestamp,
                metric.user_id,
                metric.session_id,
                metric.value,
                metric.unit,
                json.dumps(metric.context) if metric.context else None,
                json.dumps(metric.tags) if metric.tags else None
            ))
    
    def _classify_performance(self, duration_ms: float) -> str:
        """Classifica performance em tiers"""
        if duration_ms < 1000:
            return "excellent"
        elif duration_ms < 3000:
            return "good"
        elif duration_ms < 5000:
            return "acceptable"
        else:
            return "poor"
    
    def _classify_complexity(self, complexity_score: float) -> str:
        """Classifica complexidade da query"""
        if complexity_score < 0.3:
            return "simple"
        elif complexity_score < 0.7:
            return "medium"
        else:
            return "complex"
    
    def get_daily_summary(self, date: datetime = None) -> Dict[str, Any]:
        """Obtém resumo diário de métricas"""
        if not date:
            date = datetime.now().date()
        
        with duckdb.connect(self.db_path) as conn:
            # Token usage
            token_stats = conn.execute("""
                SELECT 
                    COUNT(*) as queries,
                    SUM(value) as total_tokens,
                    AVG(value) as avg_tokens,
                    SUM(CAST(JSON_EXTRACT(context_json, '$.estimated_cost') AS DOUBLE)) as total_cost
                FROM ai_metrics 
                WHERE metric_type = 'token_usage' 
                AND DATE(timestamp) = ?
            """, (date,)).fetchone()
            
            # Performance stats
            perf_stats = conn.execute("""
                SELECT 
                    AVG(value) as avg_response_time,
                    MIN(value) as min_response_time,
                    MAX(value) as max_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_response_time
                FROM ai_metrics 
                WHERE metric_type = 'response_time' 
                AND DATE(timestamp) = ?
            """, (date,)).fetchone()
            
            # Cache hit rate
            cache_stats = conn.execute("""
                SELECT AVG(value) as hit_rate
                FROM ai_metrics 
                WHERE metric_type = 'cache_hit_rate' 
                AND DATE(timestamp) = ?
            """, (date,)).fetchone()
            
            # Success rate
            success_stats = conn.execute("""
                SELECT AVG(value) as success_rate
                FROM ai_metrics 
                WHERE metric_type = 'query_accuracy' 
                AND DATE(timestamp) = ?
            """, (date,)).fetchone()
            
            # Unique users
            user_count = conn.execute("""
                SELECT COUNT(DISTINCT user_id) as unique_users
                FROM ai_metrics 
                WHERE DATE(timestamp) = ?
            """, (date,)).fetchone()
            
            return {
                "date": date.isoformat(),
                "queries": token_stats[0] if token_stats[0] else 0,
                "total_tokens": token_stats[1] if token_stats[1] else 0,
                "avg_tokens_per_query": token_stats[2] if token_stats[2] else 0,
                "total_cost_usd": token_stats[3] if token_stats[3] else 0.0,
                "avg_response_time_ms": perf_stats[0] if perf_stats[0] else 0,
                "min_response_time_ms": perf_stats[1] if perf_stats[1] else 0,
                "max_response_time_ms": perf_stats[2] if perf_stats[2] else 0,
                "p95_response_time_ms": perf_stats[3] if perf_stats[3] else 0,
                "cache_hit_rate": cache_stats[0] if cache_stats[0] else 0.0,
                "success_rate": success_stats[0] if success_stats[0] else 0.0,
                "unique_users": user_count[0] if user_count[0] else 0
            }
    
    def get_cost_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Obtém tendências de custo dos últimos N dias"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        with duckdb.connect(self.db_path) as conn:
            results = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as queries,
                    SUM(value) as total_tokens,
                    SUM(CAST(JSON_EXTRACT(context_json, '$.estimated_cost') AS DOUBLE)) as cost_usd,
                    AVG(value) as avg_tokens_per_query
                FROM ai_metrics 
                WHERE metric_type = 'token_usage' 
                AND DATE(timestamp) BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (start_date, end_date)).fetchall()
            
            return [
                {
                    "date": row[0].isoformat(),
                    "queries": row[1],
                    "total_tokens": row[2],
                    "cost_usd": row[3] or 0.0,
                    "avg_tokens_per_query": row[4]
                }
                for row in results
            ]
    
    def get_optimization_impact(self) -> Dict[str, Any]:
        """Analisa impacto das otimizações implementadas"""
        with duckdb.connect(self.db_path) as conn:
            # Compara antes/depois da otimização
            optimized_metrics = conn.execute("""
                SELECT 
                    AVG(value) as avg_tokens,
                    AVG(CAST(JSON_EXTRACT(context_json, '$.estimated_cost') AS DOUBLE)) as avg_cost,
                    COUNT(*) as sample_size
                FROM ai_metrics 
                WHERE metric_type = 'token_usage' 
                AND JSON_EXTRACT(tags_json, '$.optimization') = 'True'
                AND timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
            """).fetchone()
            
            non_optimized_metrics = conn.execute("""
                SELECT 
                    AVG(value) as avg_tokens,
                    AVG(CAST(JSON_EXTRACT(context_json, '$.estimated_cost') AS DOUBLE)) as avg_cost,
                    COUNT(*) as sample_size
                FROM ai_metrics 
                WHERE metric_type = 'token_usage' 
                AND JSON_EXTRACT(tags_json, '$.optimization') = 'False'
                AND timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
            """).fetchone()
            
            if optimized_metrics[0] and non_optimized_metrics[0]:
                token_savings = (non_optimized_metrics[0] - optimized_metrics[0]) / non_optimized_metrics[0]
                cost_savings = (non_optimized_metrics[1] - optimized_metrics[1]) / non_optimized_metrics[1]
                
                return {
                    "token_reduction_percent": token_savings * 100,
                    "cost_reduction_percent": cost_savings * 100,
                    "optimized_queries": optimized_metrics[2],
                    "non_optimized_queries": non_optimized_metrics[2],
                    "avg_tokens_optimized": optimized_metrics[0],
                    "avg_tokens_non_optimized": non_optimized_metrics[0],
                    "avg_cost_optimized": optimized_metrics[1],
                    "avg_cost_non_optimized": non_optimized_metrics[1]
                }
            
            return {"status": "insufficient_data"}
    
    def get_user_insights(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Obtém insights específicos de um usuário"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with duckdb.connect(self.db_path) as conn:
            user_stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN metric_type = 'token_usage' THEN value ELSE 0 END) as total_tokens,
                    AVG(CASE WHEN metric_type = 'response_time' THEN value ELSE NULL END) as avg_response_time,
                    AVG(CASE WHEN metric_type = 'query_accuracy' THEN value ELSE NULL END) as success_rate,
                    SUM(CASE WHEN metric_type = 'cost_tracking' THEN value ELSE 0 END) as total_cost
                FROM ai_metrics 
                WHERE user_id = ? 
                AND timestamp BETWEEN ? AND ?
            """, (user_id, start_date, end_date)).fetchone()
            
            return {
                "user_id": user_id,
                "period_days": days,
                "sessions": user_stats[0] or 0,
                "total_queries": user_stats[1] or 0,
                "total_tokens": user_stats[2] or 0,
                "avg_response_time_ms": user_stats[3] or 0,
                "success_rate": user_stats[4] or 0,
                "total_cost_usd": user_stats[5] or 0,
                "avg_queries_per_session": (user_stats[1] / max(user_stats[0], 1)) if user_stats[0] else 0,
                "avg_tokens_per_query": (user_stats[2] / max(user_stats[1], 1)) if user_stats[1] else 0
            }

# Instância global do coletor de métricas
metrics_collector = AIMetricsCollector()

# Alias para compatibilidade com imports existentes
ai_metrics = metrics_collector