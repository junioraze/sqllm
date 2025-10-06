#!/usr/bin/env python3
"""Sistema de assinaturas integrado com DuckDB"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from user_database import db
from auth_system import get_current_user
from deepseek_theme import fix_alert_visibility

class SubscriptionSystem:
    
    @staticmethod
    def get_user_subscription_info(user_id: str = None) -> Dict:
        """Obtém informações da assinatura do usuário"""
        if not user_id:
            current_user = get_current_user()
            if not current_user:
                return SubscriptionSystem._get_default_plan()
            user_id = current_user['id']
        
        subscription = db.get_user_subscription(user_id)
        
        if subscription:
            # Converte features de JSON string para lista
            features = []
            try:
                features = json.loads(subscription['features']) if subscription['features'] else []
            except:
                features = []
            
            return {
                'subscription_id': subscription['subscription_id'],
                'plan_id': subscription['plan_id'],
                'status': subscription['plan_id'],  # Para compatibilidade
                'name': subscription['plan_name'],
                'description': subscription['plan_description'],
                'price': subscription['plan_price'],
                'daily_limit': subscription['daily_limit'],
                'features': features,
                'priority_support': subscription['priority_support'],
                'start_date': subscription['start_date'],
                'end_date': subscription['end_date'],
                'user_id': user_id
            }
        
        return SubscriptionSystem._get_default_plan()
    
    @staticmethod
    def _get_default_plan() -> Dict:
        """Retorna plano padrão (free)"""
        return {
            'subscription_id': None,
            'plan_id': 'free',
            'status': 'free',
            'name': 'Gratuito',
            'description': 'Plano gratuito com 10 consultas por dia',
            'price': 0,
            'daily_limit': 10,
            'features': ['10 consultas por dia', 'Interface básica', 'Suporte da comunidade'],
            'priority_support': False,
            'start_date': None,
            'end_date': None,
            'user_id': None
        }
    
    @staticmethod
    def check_query_permission(user_id: str = None) -> Tuple[bool, str]:
        """Verifica se usuário pode fazer consulta"""
        if not user_id:
            current_user = get_current_user()
            if not current_user:
                return False, "Usuário não autenticado"
            user_id = current_user['id']
        
        # Obtém assinatura do usuário
        subscription = SubscriptionSystem.get_user_subscription_info(user_id)
        daily_limit = subscription['daily_limit']
        
        # Se é ilimitado (-1), sempre pode consultar
        if daily_limit == -1:
            return True, "Consultas ilimitadas"
        
        # Verifica uso diário
        daily_usage = db.get_daily_usage(user_id)
        
        if daily_usage >= daily_limit:
            return False, f"Limite diário atingido ({daily_usage}/{daily_limit}). Faça upgrade do seu plano!"
        
        return True, f"Consulta autorizada ({daily_usage + 1}/{daily_limit})"
    
    @staticmethod
    def increment_user_usage(user_id: str = None) -> int:
        """Incrementa uso do usuário"""
        if not user_id:
            current_user = get_current_user()
            if not current_user:
                return 0
            user_id = current_user['id']
        
        return db.increment_daily_usage(user_id)
    
    @staticmethod
    def get_daily_usage(user_id: str = None) -> int:
        """Obtém uso diário do usuário"""
        if not user_id:
            current_user = get_current_user()
            if not current_user:
                return 0
            user_id = current_user['id']
        
        return db.get_daily_usage(user_id)
    
    @staticmethod
    def change_user_plan(user_id: str, plan_id: str, payment_data: Dict = None) -> bool:
        """Altera plano do usuário"""
        return db.assign_plan_to_user(user_id, plan_id, payment_data)
    
    @staticmethod
    def get_available_plans() -> List[Dict]:
        """Retorna planos disponíveis"""
        plans = db.get_available_plans()
        
        # Converte features de JSON para lista
        for plan in plans:
            try:
                plan['features'] = json.loads(plan['features']) if plan['features'] else []
            except:
                plan['features'] = []
        
        return plans
    
    @staticmethod
    def check_feature_permission(feature: str, user_id: str = None) -> Tuple[bool, str]:
        """Verifica se usuário tem acesso a funcionalidade específica"""
        subscription = SubscriptionSystem.get_user_subscription_info(user_id)
        plan_id = subscription['plan_id']
        
        # Mapeamento de features por plano
        feature_access = {
            'free': ['basic_queries'],
            'basic': ['basic_queries', 'excel_export', 'basic_charts'],
            'premium': ['basic_queries', 'excel_export', 'basic_charts', 'advanced_charts', 'priority_support'],
            'enterprise': ['basic_queries', 'excel_export', 'basic_charts', 'advanced_charts', 'priority_support', 'api_access', 'custom_reports']
        }
        
        allowed_features = feature_access.get(plan_id, [])
        
        if feature in allowed_features:
            return True, f"Funcionalidade '{feature}' disponível no seu plano"
        else:
            return False, f"Funcionalidade '{feature}' requer upgrade de plano"

# Funções de compatibilidade (mantém interface anterior)
def get_user_subscription_info():
    """Função de compatibilidade"""
    return SubscriptionSystem.get_user_subscription_info()

def check_query_permission():
    """Função de compatibilidade"""
    return SubscriptionSystem.check_query_permission()

def check_feature_permission(feature: str):
    """Função de compatibilidade"""
    return SubscriptionSystem.check_feature_permission(feature)

def increment_user_usage():
    """Função de compatibilidade"""
    return SubscriptionSystem.increment_user_usage()

def get_daily_usage_session(user_email: str = None):
    """Função de compatibilidade - usa user_id agora"""
    current_user = get_current_user()
    if current_user:
        return SubscriptionSystem.get_daily_usage(current_user['id'])
    return 0

def apply_subscription_restrictions():
    """Função de compatibilidade"""
    return check_query_permission()

def initialize_subscription_system():
    """Função de compatibilidade - não faz nada pois DuckDB já gerencia"""
    pass

def render_upgrade_prompt():
    """Renderiza prompt de upgrade"""
    fix_alert_visibility()
    
    subscription = get_user_subscription_info()
    
    if subscription['plan_id'] == 'free':
        st.warning("⚠️ Você atingiu o limite do plano gratuito")
        st.info("💎 Faça upgrade para ter mais consultas e funcionalidades!")
        
        if st.button("🚀 Ver Planos", key="upgrade_prompt"):
            st.switch_page("pages/planos.py")