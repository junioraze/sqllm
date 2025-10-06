"""
Sistema de Teste para Assinatura - Mock Controller
Permite facilmente testar diferentes planos e cenários
"""

import streamlit as st
from subscription_manager import get_user_subscription_info
from payment_handler import activate_mock_subscription

def render_subscription_debug_panel():
    """Renderiza painel de debug para testar assinaturas"""
    if not st.session_state.get('user_email'):
        return
    
    # Só mostra se estiver em modo debug
    if st.session_state.get('debug_mode', False):
        with st.sidebar.expander("🧪 Debug: Teste de Planos", expanded=False):
            st.markdown("**Simular diferentes planos:**")
            
            user_email = st.session_state.get('user_email', '')
            # Se não há email, cria um para debug
            if not user_email:
                user_email = 'debug@test.com'
                st.session_state['user_email'] = user_email
                st.info(f"🧪 Usando email de debug: {user_email}")
            
            current_info = get_user_subscription_info()
            
            st.write(f"**Plano atual:** {current_info['description']}")
            st.write(f"**Limite diário:** {current_info['daily_limit']}")
            
            # Botões para simular diferentes planos
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⭐ Premium", key="debug_premium"):
                    simulate_plan_change(user_email, 'premium')
                    st.rerun()
                
                if st.button("📊 Básico", key="debug_basic"):
                    simulate_plan_change(user_email, 'basic')
                    st.rerun()
            
            with col2:
                if st.button("👑 Enterprise", key="debug_enterprise"):
                    simulate_plan_change(user_email, 'enterprise')
                    st.rerun()
                
                # Reset para plano gratuito (nome simplificado)
                if st.button("🆓 Free", key="debug_free"):
                    simulate_plan_change(user_email, 'free')
                    st.rerun()

def simulate_plan_change(user_email: str, plan_id: str):
    """Simula mudança para um plano específico"""
    # Se não há email, usa um email de teste para debug
    if not user_email:
        user_email = 'debug@test.com'
        st.session_state['user_email'] = user_email
    
    activate_mock_subscription(user_email, plan_id)
    st.success(f"✅ Plano alterado para: {plan_id.upper()}")
    
    # Força atualização do session_state
    st.session_state['subscription_status'] = plan_id

def enable_debug_mode():
    """Habilita modo debug"""
    st.session_state.debug_mode = True

def create_test_scenarios():
    """Cria cenários de teste para demonstração"""
    user_email = st.session_state.get('user_email', '')
    if not user_email:
        return
    
    # Cenários de teste
    scenarios = {
        'free_user': {
            'status': 'free',
            'description': 'Usuário gratuito - 10 queries/dia'
        },
        'basic_user': {
            'status': 'basic', 
            'description': 'Usuário básico - 50 queries/dia + Excel'
        },
        'premium_user': {
            'status': 'premium',
            'description': 'Usuário premium - 200 queries/dia + todos recursos'
        },
        'enterprise_user': {
            'status': 'enterprise',
            'description': 'Usuário enterprise - 1000 queries/dia + customizações'
        }
    }
    
    return scenarios

# Atalho para habilitar debug rapidamente
def quick_debug_setup():
    """Setup rápido para modo debug"""
    if st.sidebar.button("🧪 Ativar Debug", key="enable_debug"):
        enable_debug_mode()
        st.rerun()

def test_upgrade_flow():
    """Testa o fluxo completo de upgrade"""
    user_email = st.session_state.get('user_email', '')
    if not user_email:
        return False
    
    # Simula um usuário free que atingiu o limite
    simulate_plan_change(user_email, 'free')
    return True

def demonstrate_feature_restrictions():
    """Demonstra as restrições de funcionalidades"""
    from subscription_manager import check_feature_permission
    
    features_to_test = ['excel_export', 'advanced_charts', 'priority_support', 'api_access']
    
    results = {}
    for feature in features_to_test:
        has_permission, message = check_feature_permission(feature)
        results[feature] = {
            'allowed': has_permission,
            'message': message
        }
    
    return results