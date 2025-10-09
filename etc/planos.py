#!/usr/bin/env python3
"""Página de Planos - FUNCIONAL E SIMPLES"""
import streamlit as st
from datetime import datetime
from config import is_empresarial_mode
from config_menu import apply_user_preferences, initialize_user_config
from auth_system import get_current_user
from subscription_system_db import SubscriptionSystem
from deepseek_theme import create_usage_indicator, render_theme_selector, apply_selected_theme  # ESTA É A IMPORTAÇÃO CORRETA

if is_empresarial_mode():
    st.stop()
else:
    st.set_page_config(page_title="Planos", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

    # Configura nome da página no menu lateral
    if hasattr(st, '_set_page_label'):
        st._set_page_label("💳 Planos")
    else:
        # Workaround para versões antigas do Streamlit
        if 'page_label' not in st.session_state:
            st.session_state.page_label = "💳 Planos"

    # Importações corretas - SUBSCRIPTION_SYSTEM_DB NÃO TEM create_usage_indicator

    # Aplica CSS usando método que SEMPRE funciona
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #000000, #1a1a1a); color: white; }
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stMainMenu, button[title="View fullscreen"], header[data-testid="stHeader"] { display: none !important; }
    .stButton > button { background: linear-gradient(45deg, #00d4ff, #0099cc) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: bold !important; }
    .stButton > button:hover { background: linear-gradient(45deg, #00a8cc, #007799) !important; transform: translateY(-2px) !important; }
    h1, h2 { color: #00d4ff !important; }
    </style>
    """, unsafe_allow_html=True)

    # Auth check
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("❌ Faça login para acessar esta página")
        if st.button("🏠 Voltar ao Login"):
            st.switch_page("main.py")
        st.stop()

    # Inicializa configurações do usuário
    current_user = get_current_user()
    if current_user:
        st.session_state.user_email = current_user['email']
        initialize_user_config()
    else:
        st.error("❌ Erro na autenticação")
        st.stop()

    # Aplica preferências do usuário (incluindo tema)
    apply_user_preferences()

    # SIDEBAR ÚNICO E LIMPO - IGUAL AO MAIN.PY
    with st.sidebar:
        # 1. CONFIGURAÇÕES (apenas tema)
        st.markdown("### ⚙️ Configurações")
        st.markdown("**🎨 Tema Visual**")
        render_theme_selector()
        apply_selected_theme()
        current_theme = st.session_state.get('theme_mode', 'escuro')
        st.caption(f"💡 Tema {current_theme} ativo")
        
        # 2. ASSINATURA
        st.markdown("---")
        st.markdown("### 💳 Assinatura")
        
        current_user = get_current_user()
        if current_user:
            # Força atualização das informações após upgrade
            subscription_info = SubscriptionSystem.get_user_subscription_info(current_user['id'])
            
            # Mostra plano atual com destaque visual
            col1, col2 = st.columns([2, 1])
            with col1:
                plan_color = "#00d4ff" if subscription_info['plan_id'] != 'free' else "#6b7280"
                st.markdown(f"**<span style='color: {plan_color}'>{subscription_info['name']}</span>**", unsafe_allow_html=True)
                st.write(f"R$ {subscription_info['price']:.2f}/mês")
            with col2:
                if st.button("⚙️", key="manage_plan", help="Gerenciar plano"):
                    st.rerun()  # Já está na página de planos
            
            # Botão para voltar ao agente
            if st.button("🤖 Voltar ao Agente", key="sidebar_chat", use_container_width=True):
                st.switch_page("main.py")

            # 3. USO DIÁRIO - ATUALIZADO EM TEMPO REAL
            st.markdown("### 📊 Uso Diário")
            current_usage_count = SubscriptionSystem.get_daily_usage(current_user['id'])
            st.markdown(create_usage_indicator(
                current_usage_count, 
                subscription_info['daily_limit'], 
                subscription_info
            ), unsafe_allow_html=True)
            
            # 4. USUÁRIO E LOGOUT (ÚNICO)
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"👤 **{current_user['username']}**")
            with col2:
                from auth_system import logout_user
                if st.button("🚪", key="unique_logout_plans", help="Sair"):
                    logout_user()

    st.title("💳 Escolha seu Plano")

    # Dados dos planos ALINHADOS COM O BANCO DE DADOS
    planos = [
        {"nome": "Gratuito", "preco": "0", "cor": "#6b7280", "badge": "BÁSICO", "desc": "Ideal para começar", "features": ["10 consultas/dia", "Interface básica", "Suporte da comunidade"]},
        {"nome": "Premium", "preco": "59", "cor": "#00d4ff", "badge": "RECOMENDADO", "desc": "Para uso profissional", "features": ["200 consultas/dia", "Relatórios avançados", "Suporte prioritário", "Exportação de dados"]},
        {"nome": "Enterprise", "preco": "199", "cor": "#f59e0b", "badge": "MAIS POPULAR", "desc": "Sem limites", "features": ["Consultas ilimitadas", "Relatórios personalizados", "Suporte 24/7", "API dedicada"]}
    ]

    # Layout em colunas
    cols = st.columns(3)

    for i, plano in enumerate(planos):
        with cols[i]:
            # Card HTML com espaçamento uniforme e sem gaps extras
            card_html = f'<div style="border: 3px solid {plano["cor"]}; border-radius: 15px; padding: 20px; margin: 10px 0; background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(0, 212, 255, 0.02)); height: 450px; box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1); display: flex; flex-direction: column; box-sizing: border-box; width: 100%; overflow: hidden;"><div style="background: {plano["cor"]}; color: white; padding: 8px 15px; border-radius: 12px; text-align: center; font-size: 11px; font-weight: bold; margin-bottom: 12px; line-height: 1;">{plano["badge"]}</div><h2 style="text-align: center; color: {plano["cor"]}; margin: 0 0 12px 0; font-size: 24px; line-height: 1.2;">{plano["nome"]}</h2><div style="text-align: center; margin-bottom: 12px; line-height: 1;"><span style="font-size: 36px; font-weight: bold; color: #00d4ff; line-height: 1;">R$ {plano["preco"]}</span><span style="color: #888; font-size: 16px;">/mês</span></div><p style="text-align: center; color: #ccc; margin: 0 0 15px 0; font-size: 14px; line-height: 1.3;">{plano["desc"]}</p><hr style="border: none; border-top: 1px solid rgba(0, 212, 255, 0.2); margin: 15px 0;"><div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-start;">'
            
            # Adiciona features com espaçamento uniforme
            for feature in plano["features"]:
                card_html += f'<div style="display: flex; align-items: center; margin: 6px 0; color: white; line-height: 1.2;"><span style="color: #00d4ff; margin-right: 8px; font-weight: bold; font-size: 14px;">✓</span><span style="font-size: 14px;">{feature}</span></div>'
            
            # Fecha os divs
            card_html += '</div></div>'
            
            # Renderiza o card
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Espaço mínimo antes do botão
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            
            # Botão com funcionalidade real de upgrade
            upgrade_success = False
            if st.button(f"Escolher {plano['nome']}", key=f"btn_{i}", use_container_width=True):
                # Mapear nomes para plan_ids do banco (CORRETO)
                plan_mapping = {
                    "Gratuito": "free",
                    "Premium": "premium", 
                    "Enterprise": "enterprise"
                }
                
                plan_id = plan_mapping.get(plano['nome'], 'free')
                current_user = get_current_user()
                
                if current_user:
                    # Implementa upgrade real no banco de dados
                    success = SubscriptionSystem.change_user_plan(
                        user_id=current_user['id'],
                        plan_id=plan_id,
                        payment_data={"source": "web_interface", "timestamp": str(datetime.now())}
                    )
                    
                    if success:
                        st.success(f"✅ Plano {plano['nome']} ativado com sucesso!")
                        st.balloons()
                        upgrade_success = True
                        # Força recarregamento da página para atualizar sidebar
                        st.rerun()
                    else:
                        st.error("❌ Erro ao ativar plano. Tente novamente.")
                else:
                    st.error("❌ Erro na autenticação. Faça login novamente.")