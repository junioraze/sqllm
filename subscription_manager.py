#!/usr/bin/env python3
"""
Sistema de Integração de Assinatura com Requests usando session_state
Controla acesso, limites e funcionalidades baseado no plano do usuário
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Tuple, Optional

# Configurações dos planos
SUBSCRIPTION_PLANS = {
    'free': {
        'status': 'free',
        'description': 'Plano Gratuito',
        'daily_limit': 10,
        'features': ['Consultas básicas', 'Interface padrão'],
        'price': 0
    },
    'basic': {
        'status': 'basic',
        'description': 'Plano Básico',
        'daily_limit': 50,
        'features': ['Consultas básicas', 'Exportação Excel', 'Gráficos simples'],
        'price': 29.90
    },
    'premium': {
        'status': 'premium',
        'description': 'Plano Premium',
        'daily_limit': 200,
        'features': ['Consultas ilimitadas', 'Suporte prioritário', 'Relatórios detalhados', 'Gráficos avançados'],
        'price': 79.90
    },
    'enterprise': {
        'status': 'enterprise',
        'description': 'Plano Empresarial',
        'daily_limit': 1000,
        'features': ['Consultas ilimitadas', 'Suporte 24/7', 'API dedicada', 'Relatórios personalizados'],
        'price': 199.90
    }
}

def init_subscription_system():
    """Inicializa o sistema de assinatura no session_state"""
    if 'user_subscriptions' not in st.session_state:
        st.session_state['user_subscriptions'] = {}
    
    if 'daily_usage' not in st.session_state:
        st.session_state['daily_usage'] = {}
    
    if 'subscription_history' not in st.session_state:
        st.session_state['subscription_history'] = []

def get_user_subscription_info():
    """Obtém informações completas da assinatura do usuário usando session_state"""
    user_email = st.session_state.get('user_email', '')
    
    if not user_email:
        return SUBSCRIPTION_PLANS['free']
    
    # Busca assinatura no session_state
    user_subscriptions = st.session_state.get('user_subscriptions', {})
    subscription = user_subscriptions.get(user_email, {})
    
    if subscription:
        plan_type = subscription.get('plan_type', 'free')
        # Retorna dados do plano com informações do session_state
        plan_info = SUBSCRIPTION_PLANS.get(plan_type, SUBSCRIPTION_PLANS['free']).copy()
        plan_info.update({
            'user_email': user_email,
            'start_date': subscription.get('start_date'),
            'end_date': subscription.get('end_date'),
            'created_at': subscription.get('created_at')
        })
        return plan_info
    
    return SUBSCRIPTION_PLANS['free']

def save_user_subscription_session(user_email: str, plan_type: str, status: str = 'active'):
    """Salva assinatura do usuário no session_state"""
    if 'user_subscriptions' not in st.session_state:
        st.session_state['user_subscriptions'] = {}
    
    subscription_data = {
        'plan_type': plan_type,
        'status': status,
        'start_date': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    st.session_state['user_subscriptions'][user_email] = subscription_data
    
    # Adiciona ao histórico
    add_subscription_history_session(user_email, 'plan_updated', plan_type, f'Plano atualizado para {plan_type}')
    
    return True

def get_daily_usage_session(user_email: str) -> int:
    """Obtém uso diário do usuário do session_state"""
    if 'daily_usage' not in st.session_state:
        st.session_state['daily_usage'] = {}
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_key = f"{user_email}_{today}"
    
    return st.session_state['daily_usage'].get(user_key, 0)

def increment_daily_usage_session(user_email: str):
    """Incrementa uso diário do usuário no session_state"""
    if 'daily_usage' not in st.session_state:
        st.session_state['daily_usage'] = {}
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_key = f"{user_email}_{today}"
    
    current_usage = st.session_state['daily_usage'].get(user_key, 0)
    st.session_state['daily_usage'][user_key] = current_usage + 1

def add_subscription_history_session(user_email: str, action: str, plan_type: str = None, details: str = None):
    """Adiciona evento ao histórico de assinatura no session_state"""
    if 'subscription_history' not in st.session_state:
        st.session_state['subscription_history'] = []
    
    history_entry = {
        'user_email': user_email,
        'action': action,
        'plan_type': plan_type,
        'details': details,
        'created_at': datetime.now().isoformat()
    }
    
    st.session_state['subscription_history'].append(history_entry)

def check_query_permission():
    """Verifica se o usuário pode fazer mais consultas hoje usando session_state"""
    user_email = st.session_state.get('user_email', '')
    subscription_info = get_user_subscription_info()
    
    if not user_email:
        # Usuário anônimo - limite global
        return check_global_rate_limit()
    
    # Usuário logado - verifica uso individual no session_state
    daily_usage = get_daily_usage_session(user_email)
    daily_limit = subscription_info['daily_limit']
    
    if daily_usage >= daily_limit:
        return False, f"Limite diário de {daily_limit} consultas atingido. Faça upgrade do seu plano."
    
    return True, f"Consultas restantes hoje: {daily_limit - daily_usage}"

def increment_user_usage():
    """Incrementa o uso do usuário no session_state"""
    user_email = st.session_state.get('user_email', '')
    
    if user_email:
        # Usuário logado - incrementa no session_state
        increment_daily_usage_session(user_email)
        
        # Adiciona ao histórico
        add_subscription_history_session(
            user_email, 
            'query_executed', 
            details=f"Query executada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        # Usuário anônimo - incrementa contador global
        increment_global_usage()

def check_global_rate_limit():
    """Verifica limite global para usuários anônimos"""
    if 'global_usage' not in st.session_state:
        st.session_state['global_usage'] = 0
    
    if 'global_usage_date' not in st.session_state:
        st.session_state['global_usage_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Reset diário
    today = datetime.now().strftime('%Y-%m-%d')
    if st.session_state['global_usage_date'] != today:
        st.session_state['global_usage'] = 0
        st.session_state['global_usage_date'] = today
    
    global_limit = 100  # Limite global para usuários anônimos
    
    if st.session_state['global_usage'] >= global_limit:
        return False, "Limite global atingido. Faça login para continuar."
    
    return True, f"Consultas restantes (global): {global_limit - st.session_state['global_usage']}"

def increment_global_usage():
    """Incrementa contador global para usuários anônimos"""
    if 'global_usage' not in st.session_state:
        st.session_state['global_usage'] = 0
    
    st.session_state['global_usage'] += 1

def can_user_access_feature(feature_name: str) -> bool:
    """Verifica se usuário pode acessar uma funcionalidade específica"""
    subscription_info = get_user_subscription_info()
    user_features = subscription_info.get('features', [])
    
    # Mapeamento de funcionalidades
    feature_mapping = {
        'export_excel': 'Exportação Excel',
        'advanced_charts': 'Gráficos avançados',
        'priority_support': 'Suporte prioritário',
        'detailed_reports': 'Relatórios detalhados',
        'api_access': 'API dedicada'
    }
    
    required_feature = feature_mapping.get(feature_name, feature_name)
    return required_feature in user_features

def check_feature_permission(feature_name: str) -> Tuple[bool, str]:
    """Verifica se usuário tem permissão para usar uma funcionalidade específica"""
    subscription_info = get_user_subscription_info()
    user_features = subscription_info.get('features', [])
    
    # Mapeamento de funcionalidades
    feature_mapping = {
        'excel_export': 'Exportação Excel',
        'advanced_charts': 'Gráficos avançados',
        'priority_support': 'Suporte prioritário',
        'detailed_reports': 'Relatórios detalhados',
        'api_access': 'API dedicada'
    }
    
    required_feature = feature_mapping.get(feature_name, feature_name)
    has_permission = required_feature in user_features
    
    if has_permission:
        return True, f"Funcionalidade '{required_feature}' disponível no seu plano {subscription_info['description']}"
    else:
        return False, f"Funcionalidade '{required_feature}' não disponível no seu plano {subscription_info['description']}. Faça upgrade para acessar."

def get_subscription_status():
    """Retorna status resumido da assinatura para UI"""
    subscription_info = get_user_subscription_info()
    user_email = st.session_state.get('user_email', '')
    
    if not user_email:
        return {
            'is_logged_in': False,
            'plan': 'free',
            'status': 'Usuário Anônimo',
            'usage_today': st.session_state.get('global_usage', 0),
            'daily_limit': 100
        }
    
    daily_usage = get_daily_usage_session(user_email)
    
    return {
        'is_logged_in': True,
        'plan': subscription_info['status'],
        'status': subscription_info['description'],
        'usage_today': daily_usage,
        'daily_limit': subscription_info['daily_limit'],
        'features': subscription_info['features']
    }

def upgrade_user_plan(user_email: str, new_plan: str):
    """Atualiza plano do usuário"""
    if new_plan not in SUBSCRIPTION_PLANS:
        return False, f"Plano {new_plan} não existe"
    
    success = save_user_subscription_session(user_email, new_plan, 'active')
    
    if success:
        return True, f"Plano atualizado para {SUBSCRIPTION_PLANS[new_plan]['description']}"
    
    return False, "Erro ao atualizar plano"

def apply_subscription_restrictions():
    """Aplica restrições baseadas no plano de assinatura"""
    subscription_info = get_user_subscription_info()
    user_email = st.session_state.get('user_email', '')
    
    # Se não há usuário logado, aplica restrições de usuário anônimo
    if not user_email:
        return check_global_rate_limit()
    
    # Verifica permissões de consulta
    return check_query_permission()

def initialize_subscription_system():
    """Inicializa o sistema de assinatura - alias para compatibilidade"""
    return init_subscription_system()

def render_upgrade_prompt():
    """Renderiza prompt de upgrade de plano"""
    subscription_info = get_user_subscription_info()
    
    if subscription_info['status'] == 'free':
        st.warning("🚀 **Faça upgrade para o plano Premium!**")
        st.markdown("**Benefícios do Premium:**")
        st.markdown("• 200 consultas por dia (vs 10 no gratuito)")
        st.markdown("• Suporte prioritário")
        st.markdown("• Relatórios detalhados")
        st.markdown("• Gráficos avançados")
        
        if st.button("🎯 Fazer Upgrade Agora"):
            st.switch_page("pages/pagamentos.py")

# Alias para compatibilidade
def get_daily_usage(user_email: str) -> int:
    """Alias para compatibilidade"""
    return get_daily_usage_session(user_email)

# Inicializa o sistema ao importar
init_subscription_system()