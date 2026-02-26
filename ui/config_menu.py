#!/usr/bin/env python3
"""Sistema de Configurações - APENAS FUNÇÕES AUXILIARES"""
import streamlit as st
from ui.deepseek_theme import apply_selected_theme

def apply_user_preferences():
    """Aplica preferências do usuário - SIMPLES"""
    theme_mode = st.session_state.get('theme_mode', 'escuro')
    apply_selected_theme(theme_mode)

def initialize_user_config():
    """Inicializa configurações básicas"""
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'escuro'

def check_feature_access(feature_name):
    """Verifica acesso a funcionalidades premium"""
    from utils.subscription_system_db import SubscriptionSystem
    from utils.auth_system import get_current_user
    
    current_user = get_current_user()
    if current_user:
        subscription_info = SubscriptionSystem.get_user_subscription_info(current_user['id'])
        if subscription_info['plan_id'] != 'free':
            return True
    
    st.warning(f"⚠️ {feature_name} disponível apenas para planos pagos")
    return False