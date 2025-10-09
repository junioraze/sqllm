#!/usr/bin/env python3
"""Sistema de banco de dados para usuários e assinaturas usando DuckDB"""

import duckdb
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class UserDatabase:
    def __init__(self, db_path: str = "users_new.db"):
        """Inicializa conexão com DuckDB"""
        self.db_path = db_path
        
        # Garante que o diretório existe apenas se não for arquivo na raiz
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        try:
            self.conn = duckdb.connect(db_path)
            print(f"✅ Banco conectado: {os.path.abspath(db_path)}")
            self._create_tables()
        except Exception as e:
            print(f"❌ Erro ao conectar com banco: {e}")
            # Fallback para banco em memória
            print("🔄 Usando banco em memória como fallback")
            self.conn = duckdb.connect(":memory:")
            self._create_tables()

    def _create_tables(self):
        """Cria as tabelas necessárias"""
        
        # Tabela de usuários
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        # Tabela de planos disponíveis
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                daily_limit INTEGER NOT NULL,
                features TEXT, -- JSON string
                priority_support BOOLEAN DEFAULT false,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de assinaturas dos usuários
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                plan_id VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                payment_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de uso diário
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                usage_date DATE DEFAULT CURRENT_DATE,
                query_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, usage_date)
            )
        """)
        
        # Inicializa planos padrão se não existirem
        self._init_default_plans()

    def _init_default_plans(self):
        """Inicializa planos padrão no banco"""
        plans = [
            {
                'id': 'free',
                'name': 'Gratuito',
                'description': 'Plano gratuito com 10 consultas por dia',
                'price': 0.00,
                'daily_limit': 10,
                'features': '["10 consultas por dia", "Interface básica", "Suporte da comunidade"]',
                'priority_support': False
            },
            {
                'id': 'basic',
                'name': 'Básico',
                'description': 'Acesso básico com 50 consultas por dia',
                'price': 29.90,
                'daily_limit': 50,
                'features': '["50 consultas por dia", "Relatórios básicos", "Suporte por email"]',
                'priority_support': False
            },
            {
                'id': 'premium',
                'name': 'Premium',
                'description': 'Acesso premium com 200 consultas por dia',
                'price': 59.90,
                'daily_limit': 200,
                'features': '["200 consultas por dia", "Relatórios avançados", "Suporte prioritário", "Exportação de dados"]',
                'priority_support': True
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise',
                'description': 'Acesso empresarial ilimitado',
                'price': 199.90,
                'daily_limit': -1,  # -1 = ilimitado
                'features': '["Consultas ilimitadas", "Relatórios personalizados", "Suporte 24/7", "API dedicada"]',
                'priority_support': True
            }
        ]
        
        for plan in plans:
            # Verifica se plano já existe
            existing = self.conn.execute("SELECT id FROM subscription_plans WHERE id = ?", [plan['id']]).fetchone()
            if not existing:
                self.conn.execute("""
                    INSERT INTO subscription_plans (id, name, description, price, daily_limit, features, priority_support)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [plan['id'], plan['name'], plan['description'], plan['price'], 
                     plan['daily_limit'], plan['features'], plan['priority_support']])

    def _hash_password(self, password: str) -> str:
        """Hash da senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """Cria novo usuário"""
        try:
            # Verifica se usuário já existe
            existing = self.conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", 
                [username, email]
            ).fetchone()
            
            if existing:
                return False, "Usuário ou email já existe"
            
            # Cria novo usuário
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(password)
            
            self.conn.execute("""
                INSERT INTO users (id, username, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, [user_id, username, email, password_hash])
            
            # Atribui plano gratuito por padrão
            self.assign_plan_to_user(user_id, 'free')
            
            return True, "Usuário criado com sucesso"
            
        except Exception as e:
            return False, f"Erro ao criar usuário: {str(e)}"

    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Autentica usuário por username ou email"""
        try:
            password_hash = self._hash_password(password)
            
            user = self.conn.execute("""
                SELECT id, username, email, created_at, is_active
                FROM users 
                WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = true
            """, [username_or_email, username_or_email, password_hash]).fetchone()
            
            if user:
                return True, {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3],
                    'is_active': user[4]
                }
            else:
                return False, None
                
        except Exception as e:
            return False, None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtém usuário pelo username"""
        try:
            user = self.conn.execute("""
                SELECT id, username, email, created_at, is_active
                FROM users 
                WHERE username = ? AND is_active = true
            """, [username]).fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3],
                    'is_active': user[4]
                }
            return None
        except:
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Obtém usuário pelo email"""
        try:
            user = self.conn.execute("""
                SELECT id, username, email, created_at, is_active
                FROM users 
                WHERE email = ? AND is_active = true
            """, [email]).fetchone()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3],
                    'is_active': user[4]
                }
            return None
        except:
            return None

    def assign_plan_to_user(self, user_id: str, plan_id: str, payment_data: Dict = None) -> bool:
        """Atribui plano a um usuário"""
        try:
            # Cancela assinatura ativa atual
            self.conn.execute("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status = 'active'
            """, [user_id])
            
            # Cria nova assinatura
            subscription_id = str(uuid.uuid4())
            payment_json = str(payment_data) if payment_data else None
            
            self.conn.execute("""
                INSERT INTO user_subscriptions (id, user_id, plan_id, payment_data)
                VALUES (?, ?, ?, ?)
            """, [subscription_id, user_id, plan_id, payment_json])
            
            return True
        except Exception as e:
            print(f"Erro ao atribuir plano: {e}")
            return False

    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Obtém assinatura ativa do usuário"""
        try:
            result = self.conn.execute("""
                SELECT 
                    us.id, us.plan_id, us.status, us.start_date, us.end_date,
                    sp.name, sp.description, sp.price, sp.daily_limit, 
                    sp.features, sp.priority_support
                FROM user_subscriptions us
                JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE us.user_id = ? AND us.status = 'active'
                ORDER BY us.created_at DESC
                LIMIT 1
            """, [user_id]).fetchone()
            
            if result:
                return {
                    'subscription_id': result[0],
                    'plan_id': result[1],
                    'status': result[2],
                    'start_date': result[3],
                    'end_date': result[4],
                    'plan_name': result[5],
                    'plan_description': result[6],
                    'plan_price': result[7],
                    'daily_limit': result[8],
                    'features': result[9],
                    'priority_support': result[10]
                }
            return None
        except Exception as e:
            print(f"Erro ao obter assinatura: {e}")
            return None

    def get_daily_usage(self, user_id: str, date: str = None) -> int:
        """Obtém uso diário do usuário"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            result = self.conn.execute("""
                SELECT query_count FROM daily_usage
                WHERE user_id = ? AND usage_date = ?
            """, [user_id, date]).fetchone()
            
            return result[0] if result else 0
        except:
            return 0

    def increment_daily_usage(self, user_id: str, increment: int = 1) -> int:
        """Incrementa uso diário e retorna total"""
        date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().isoformat()
        
        try:
            # Verifica se registro já existe
            existing = self.conn.execute("""
                SELECT query_count FROM daily_usage
                WHERE user_id = ? AND usage_date = ?
            """, [user_id, date]).fetchone()
            
            if existing:
                # Atualiza registro existente
                new_count = existing[0] + increment
                self.conn.execute("""
                    UPDATE daily_usage 
                    SET query_count = ?, updated_at = ?
                    WHERE user_id = ? AND usage_date = ?
                """, [new_count, current_time, user_id, date])
                return new_count
            else:
                # Insere novo registro
                self.conn.execute("""
                    INSERT INTO daily_usage (id, user_id, usage_date, query_count, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, [str(uuid.uuid4()), user_id, date, increment, current_time])
                return increment
                
        except Exception as e:
            print(f"Erro ao incrementar uso: {e}")
            return 0

    def get_available_plans(self) -> List[Dict]:
        """Retorna todos os planos disponíveis"""
        try:
            results = self.conn.execute("""
                SELECT id, name, description, price, daily_limit, features, priority_support
                FROM subscription_plans
                WHERE is_active = true
                ORDER BY price ASC
            """).fetchall()
            
            plans = []
            for row in results:
                plans.append({
                    'plan_id': row[0],  # Mudança: usando 'plan_id' em vez de 'id'
                    'name': row[1],
                    'description': row[2],
                    'price': row[3],
                    'daily_limit': row[4],
                    'features': row[5],
                    'priority_support': row[6]
                })
            
            return plans
        except:
            return []

    def create_plan(self, plan_id: str, name: str, description: str, price: float, 
                   daily_limit: int, features: str, priority_support: bool = False) -> bool:
        """Cria um novo plano de assinatura"""
        try:
            self.conn.execute("""
                INSERT INTO subscription_plans (id, name, description, price, daily_limit, features, priority_support)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [plan_id, name, description, price, daily_limit, features, priority_support])
            return True
        except Exception as e:
            print(f"Erro ao criar plano: {e}")
            return False

    def close(self):
        """Fecha conexão com banco"""
        if self.conn:
            self.conn.close()

# Instância global do banco
db = UserDatabase()