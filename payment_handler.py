#!/usr/bin/env python3
"""Sistema de Pagamentos - Mock Version usando session_state"""
import streamlit as st
import uuid
from typing import Dict, List, Optional
from mercadopago_mock import MOCK_PLANS, simulate_payment_flow

def get_available_plans() -> List[Dict]:
    """Retorna os planos de assinatura disponíveis"""
    plans = []
    for plan_id, plan_data in MOCK_PLANS.items():
        plans.append({
            'id': plan_data['id'],
            'name': plan_data['name'],
            'price': plan_data['price'],
            'currency': 'BRL',
            'interval': 'monthly',
            'description': plan_data['description'],
            'features': plan_data['features'],
            'highlight': plan_id == 'premium',
            'query_limit': plan_data['query_limit'],
            'priority_support': plan_data['priority_support']
        })
    return plans

def create_payment_preference(plan_id: str, user_email: str, user_name: str) -> Optional[Dict]:
    """Cria preferência de pagamento mock"""
    try:
        flow_result = simulate_payment_flow(plan_id, user_email)
        
        if flow_result.get('preference'):
            preference_data = flow_result['preference']['response']
            
            if 'mock_preferences' not in st.session_state:
                st.session_state.mock_preferences = {}
            
            st.session_state.mock_preferences[preference_data['id']] = {
                'plan_id': plan_id,
                'user_email': user_email
            }
            
            return preference_data
            
    except Exception:
        return None

def check_user_subscription(user_email: str) -> str:
    """Verifica status da assinatura do usuário"""
    if not user_email:
        return 'free'
    
    from subscription_manager import get_user_subscription_info
    subscription_info = get_user_subscription_info()
    
    return subscription_info.get('status', 'free')

def cancel_user_subscription(user_email: str) -> bool:
    """Cancela assinatura do usuário"""
    mock_subscriptions = st.session_state.get('mock_subscriptions', {})
    
    if user_email in mock_subscriptions:
        mock_subscriptions[user_email]['status'] = 'cancelled'
        st.session_state.mock_subscriptions = mock_subscriptions
        return True
    
    return False

def activate_mock_subscription(user_email: str, plan_id: str):
    """Ativa assinatura mock usando session_state"""
    if plan_id not in MOCK_PLANS:
        return False
    
    # Salva no session_state do subscription_manager
    from subscription_manager import save_user_subscription_session
    
    success = save_user_subscription_session(
        user_email=user_email,
        plan_type=plan_id,
        status='active'
    )
    
    # Também atualiza o status de assinatura do streamlit
    st.session_state['subscription_status'] = plan_id
    
    return success

def simulate_successful_payment(user_email: str, plan_id: str) -> Dict:
    """Simula um pagamento aprovado usando session_state"""
    payment_id = f"mock_pay_{uuid.uuid4().hex[:8]}"
    
    # Ativa a assinatura
    success = activate_mock_subscription(user_email, plan_id)
    
    if success:
        return {
            'success': True,
            'payment_id': payment_id,
            'status': 'approved',
            'plan_id': plan_id,
            'user_email': user_email,
            'amount': MOCK_PLANS[plan_id]['price'],
            'currency': 'BRL',
            'subscription_id': f'sub_{uuid.uuid4().hex[:8]}',
            'message': f'Pagamento aprovado! Plano {MOCK_PLANS[plan_id]["name"]} ativado.'
        }
    else:
        return {
            'success': False,
            'error': 'Erro ao ativar assinatura'
        }
    
    # Ativa assinatura e sincroniza
    activate_mock_subscription(user_email, plan_id)
    
    # Chama webhook adicional para garantir sincronização
    if SYNC_ENABLED:
        register_payment_webhook(user_email, plan_id, payment_result)
    
    return payment_result

def get_subscription_info(user_email: str) -> Dict:
    """Retorna informações da assinatura do usuário"""
    mock_subscriptions = st.session_state.get('mock_subscriptions', {})
    
    if user_email in mock_subscriptions:
        subscription = mock_subscriptions[user_email]
        plan_info = MOCK_PLANS.get(subscription['plan_id'], {})
        
        return {
            'status': subscription['status'],
            'plan_name': plan_info.get('name', 'Desconhecido'),
            'plan_id': subscription['plan_id'],
            'query_limit': plan_info.get('query_limit', 0),
            'features': plan_info.get('features', [])
        }
    
    return {
        'status': 'free',
        'plan_name': 'Gratuito',
        'plan_id': 'free',
        'query_limit': 10,
        'features': ['Acesso básico', 'Suporte por email']
    }

def is_feature_available(user_email: str, feature: str) -> bool:
    """Verifica se uma funcionalidade está disponível para o usuário"""
    subscription = get_subscription_info(user_email)
    
    if subscription['status'] == 'free':
        return feature in ['basic_queries', 'email_support']
    elif subscription['plan_id'] == 'basic':
        return feature in ['basic_queries', 'advanced_charts', 'data_export', 'email_support']
    elif subscription['plan_id'] == 'premium':
        return feature in ['advanced_queries', 'advanced_charts', 'data_export', 'priority_support', 'custom_themes']
    elif subscription['plan_id'] == 'enterprise':
        return True
    
    return False