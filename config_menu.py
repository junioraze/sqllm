#!/usr/bin/env python3
"""Sistema de Menu de Configurações - Streamlit Nativo"""
import streamlit as st
from deepseek_theme import render_theme_selector, apply_selected_theme

def render_config_menu():
    """Menu de configurações com componentes nativos"""
    
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        
        # Tabs estruturadas nativas
        tab1, tab2 = st.tabs(["🎨 Tema", "👤 Conta"])
        
        with tab1:
            render_theme_tab()
        
        with tab2:
            render_account_tab()

def render_theme_tab():
    """Aba de configurações de tema"""
    st.markdown("**Personalização Visual**")
    
    # Seletor de tema nativo
    render_theme_selector()
    
    # Aplicar configurações automaticamente
    apply_selected_theme()
    
    # Informações sobre tema
    st.info("💡 As mudanças são aplicadas automaticamente")

def render_account_tab():
    """Aba de configurações de conta"""
    st.markdown("**Gerenciar Conta**")
    
    # Status da conta
    user_email = st.session_state.get('user_email', 'usuario@exemplo.com')
    st.write(f"**Email:** {user_email}")
    
    # Botões de ação nativos
    if st.button("🔄 Redefinir Configurações", key="reset_config", use_container_width=True):
        reset_user_preferences()
        st.success("✅ Configurações redefinidas!")
        st.rerun()
    
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        handle_logout()

def reset_user_preferences():
    """Redefine preferências do usuário"""
    # Remove configurações de tema
    if 'selected_theme' in st.session_state:
        del st.session_state.selected_theme
    
    # Remove outras preferências
    preferences_keys = ['theme_preference', 'ui_mode', 'nav_page']
    for key in preferences_keys:
        if key in st.session_state:
            del st.session_state[key]

def handle_logout():
    """Processa logout do usuário"""
    # Limpa autenticação
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    
    # Limpa dados do usuário
    user_keys = ['user_email', 'subscription_status', 'queries_today']
    for key in user_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def check_feature_access(feature_name):
    """Verifica se o usuário tem acesso a uma funcionalidade"""
    from payment_handler import check_user_subscription
    
    user_email = st.session_state.get('user_email', '')
    subscription_status = check_user_subscription(user_email)
    
    if subscription_status == 'active':
        return True
    else:
        st.warning(f"⚠️ {feature_name} disponível apenas para assinantes premium")
        return False
        
        with tab1:
            render_theme_section()
        
        with tab2:
            render_account_section()

def render_theme_section():
    """Seção de tema usando componentes nativos"""
    
    render_theme_selector()
    
    current_theme = st.session_state.get('theme_mode', 'escuro')
    status_icon = "🌙" if current_theme == "escuro" else "☀️"
    status_text = f"{status_icon} Modo {current_theme} ativo"
    
    st.info(status_text)

def render_account_section():
    """Seção de conta usando componentes nativos"""
    
    subscription_status = check_user_subscription(st.session_state.get('user_email', ''))
    
    # Status da assinatura
    if subscription_status == 'active':
        st.success("✅ Assinatura Ativa")
        
        # Botão gerenciar
        if st.button("💳 Gerenciar Assinatura", use_container_width=True, key="manage_btn"):
            st.session_state.nav_page = "payment"
            st.rerun()
        
    else:
        st.info("🆓 Conta Gratuita")
        
        # Botão upgrade
        if st.button("⭐ Fazer Upgrade", use_container_width=True, key="upgrade_btn"):
            st.session_state.nav_page = "payment"
            st.rerun()
    
    # Divisor
    st.divider()
    
    # Uso diário nativo
    st.markdown("📈 **Uso Diário**")
    
    try:
        queries_used = st.session_state.get('queries_today', 0)
        daily_limit = 100 if subscription_status == 'active' else 10
        progress_value = min(queries_used / daily_limit, 1.0) if daily_limit > 0 else 0
        
        st.progress(progress_value, text=f"{queries_used}/{daily_limit} consultas utilizadas hoje")
    except Exception:
        st.caption("Informações de uso indisponíveis")
    
    # Divisor final
    st.divider()
    
    # Botão sair
    if st.button("🚪 Sair da Conta", use_container_width=True, type="secondary", key="logout_btn"):
        # Limpeza completa e segura
        st.session_state.clear()
        st.session_state.authenticated = False
        st.rerun()

def apply_user_preferences():
    """Aplica preferências do usuário"""
    theme_mode = st.session_state.get('theme_mode', 'escuro')
    apply_selected_theme(theme_mode)

def initialize_user_config():
    """Inicializa configurações do usuário"""
    defaults = {
        'theme_mode': 'escuro',
        'user_email': '',
        'user_name': ''
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def check_user_subscription(user_email):
    """Verifica status da assinatura"""
    try:
        from payment_handler import check_user_subscription as check_sub
        return check_sub(user_email)
    except Exception:
        return 'free'