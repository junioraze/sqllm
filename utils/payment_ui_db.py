#!/usr/bin/env python3
"""Interface de pagamentos e planos integrada com DuckDB"""

import streamlit as st
from typing import Dict, List
from utils.subscription_system_db import SubscriptionSystem
from utils.auth_system import get_current_user, logout_user
from utils.user_database import db
from ui.deepseek_theme import create_usage_indicator
from ui.config_menu import render_config_menu

def render_payment_ui():
    """Interface principal de pagamentos"""
    
    # Verifica autenticação
    current_user = get_current_user()
    if not current_user:
        st.error("❌ Você precisa estar logado para acessar esta página")
        return
    
    # Menu de configurações no sidebar (MESMO PADRÃO DO MAIN.PY)
    render_config_menu()
    
    # Renderiza o mesmo sidebar do main.py
    render_sidebar_menu(current_user)
    
    # Header principal
    st.title("💳 Planos e Assinaturas")
    st.markdown("Escolha o plano ideal para suas necessidades")
    
    st.divider()
    
    # Navegação
    tab1, tab2 = st.tabs(["💎 Planos Disponíveis", "👤 Minha Conta"])
    
    with tab1:
        render_plans_section()
    
    with tab2:
        render_account_section()

def render_sidebar_menu(current_user):
    """Renderiza o mesmo menu sidebar do main.py"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💳 Assinatura")
        
        subscription_info = SubscriptionSystem.get_user_subscription_info(current_user['id'])
        
        # Mostra plano atual
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{subscription_info['name']}**")
            st.write(f"R$ {subscription_info['price']:.2f}/mês")
        with col2:
            if st.button("🏠", key="go_home", help="Voltar ao Chat"):
                st.switch_page("main.py")
        
        # Indicador de uso (MESMO PADRÃO DO MAIN.PY)
        current_usage_count = SubscriptionSystem.get_daily_usage(current_user['id'])
        
        st.markdown("### 📊 Uso Diário")
        st.markdown(create_usage_indicator(
            current_usage_count, 
            subscription_info['daily_limit'], 
            subscription_info
        ), unsafe_allow_html=True)
        
        # Botão de logout
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"👤 **{current_user['username']}**")
        with col2:
            if st.button("🚪", key="sidebar_logout", help="Sair"):
                logout_user()

def render_plans_section():
    """Seção de planos disponíveis com design focado em conversão"""
    
    # Header promocional
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.3);
        ">
            <h2 style="color: white; margin: 0; font-size: 32px;">✨ Desbloqueie Todo o Potencial</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 18px;">
                Análise de dados ilimitada com IA de última geração
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    current_user = get_current_user()
    current_subscription = SubscriptionSystem.get_user_subscription_info()
    current_plan_id = current_subscription['plan_id']
    
    plans = SubscriptionSystem.get_available_plans()
    
    # Define qual plano é o "mais popular"
    popular_plan_id = 'premium'  # ou 'pro' dependendo dos planos disponíveis
    
    # Organiza planos em colunas
    cols = st.columns(len(plans))
    
    for i, plan in enumerate(plans):
        with cols[i]:
            
            # Determina o estilo do card
            is_current = plan['id'] == current_plan_id
            is_popular = plan['id'] == popular_plan_id
            is_free = plan['id'] == 'free'
            
            # Define cores e badges
            if is_current:
                border_color = "#22c55e"  # Verde para plano atual
                badge = "✅ SEU PLANO"
                badge_color = "#22c55e"
            elif is_popular and not is_free:
                border_color = "#f59e0b"  # Dourado para mais popular
                badge = "🔥 MAIS POPULAR"
                badge_color = "#f59e0b"
            elif not is_free:
                border_color = "#00d4ff"  # Azul da marca para outros premium
                badge = "⭐ RECOMENDADO"
                badge_color = "#00d4ff"
            else:
                border_color = "#6b7280"  # Cinza para free
                badge = "💡 BÁSICO"
                badge_color = "#6b7280"
            
            # Card principal com design elegante
            st.markdown(f"""
                <div style="
                    border: 3px solid {border_color}; 
                    border-radius: 20px; 
                    padding: 30px; 
                    margin: 15px 0; 
                    min-height: 500px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    position: relative;
                    overflow: hidden;
                    transform: {('scale(1.05)' if is_popular and not is_current else 'scale(1.0)')};
                    transition: transform 0.3s ease;
                ">
                    <div style="
                        background: {badge_color}; 
                        color: white; 
                        padding: 8px 16px; 
                        border-radius: 20px; 
                        font-size: 12px; 
                        font-weight: bold; 
                        text-align: center; 
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    ">{badge}</div>
                    
                    <h2 style="text-align: center; color: {border_color}; margin-bottom: 10px; font-size: 28px;">{plan['name']}</h2>
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 48px; font-weight: bold; color: white;">R$ {plan['price']:.0f}</span>
                        <span style="color: #888; font-size: 18px;">/mês</span>
                    </div>
                    
                    <p style="text-align: center; color: #ccc; font-size: 16px; margin-bottom: 25px; line-height: 1.5;">
                        {plan['description']}
                    </p>
                    
                    <hr style="border: 1px solid rgba(255,255,255,0.1); margin: 20px 0;">
                    
                    <div style="color: white;">
            """, unsafe_allow_html=True)
            
            # Lista de features estilizada
            for feature in plan['features']:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin: 12px 0; color: #e5e7eb;">
                        <span style="color: {border_color}; margin-right: 10px; font-size: 16px;">✓</span>
                        <span style="font-size: 15px;">{feature}</span>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Espaçamento antes do botão
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botão de ação com design melhorado
            if is_current:
                st.markdown(f"""
                    <div style="text-align: center;">
                        <button style="
                            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                            color: white;
                            border: none;
                            padding: 15px 30px;
                            border-radius: 50px;
                            font-size: 16px;
                            font-weight: bold;
                            cursor: not-allowed;
                            width: 100%;
                            opacity: 0.8;
                            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
                        ">✅ Seu Plano Atual</button>
                    </div>
                """, unsafe_allow_html=True)
            elif plan['id'] == 'free':
                if st.button(f"⬇️ Voltar para Gratuito", key=f"downgrade_{plan['id']}", use_container_width=True, type="secondary"):
                    change_plan(current_user['id'], plan['id'])
            else:
                # Botão premium com destaque
                button_style = "primary" if is_popular else "secondary"
                button_text = f"🚀 ASSINAR {plan['name'].upper()}" if is_popular else f"⬆️ Upgrade para {plan['name']}"
                
                if st.button(button_text, key=f"upgrade_{plan['id']}", use_container_width=True, type=button_style):
                    change_plan(current_user['id'], plan['id'])
            
            # Destaque especial para o plano mais popular
            if is_popular and not is_current:
                st.markdown("""
                    <div style="text-align: center; margin-top: 10px;">
                        <span style="color: #f59e0b; font-size: 12px; font-weight: bold;">
                            🔥 Escolha de 85% dos nossos usuários
                        </span>
                    </div>
                """, unsafe_allow_html=True)
    
    # Seção de garantia e benefícios
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 48px; margin-bottom: 10px;">🛡️</div>
                <h4 style="color: #00d4ff; margin-bottom: 10px;">Garantia 30 dias</h4>
                <p style="color: #ccc; font-size: 14px;">Satisfação garantida ou devolvemos seu dinheiro</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 48px; margin-bottom: 10px;">⚡</div>
                <h4 style="color: #00d4ff; margin-bottom: 10px;">Ativação Instantânea</h4>
                <p style="color: #ccc; font-size: 14px;">Acesso imediato a todos os recursos premium</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 48px; margin-bottom: 10px;">🎯</div>
                <h4 style="color: #00d4ff; margin-bottom: 10px;">Suporte Especializado</h4>
                <p style="color: #ccc; font-size: 14px;">Equipe dedicada para te ajudar 24/7</p>
            </div>
        """, unsafe_allow_html=True)

def render_account_section():
    """Seção da conta do usuário"""
    
    current_user = get_current_user()
    subscription = SubscriptionSystem.get_user_subscription_info()
    
    st.subheader("📊 Status da Conta")
    
    # Informações da assinatura
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Plano", subscription['name'])
    
    with col2:
        daily_usage = SubscriptionSystem.get_daily_usage()
        st.metric("Consultas Hoje", daily_usage)
    
    with col3:
        daily_limit = subscription['daily_limit']
        limit_text = "Ilimitado" if daily_limit == -1 else str(daily_limit)
        st.metric("Limite Diário", limit_text)
    
    with col4:
        if daily_limit == -1:
            remaining = "∞"
        else:
            remaining = max(0, daily_limit - daily_usage)
        st.metric("Disponível", remaining)
    
    st.divider()
    
    # Detalhes da conta
    st.subheader("👤 Detalhes da Conta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Nome de usuário:** {current_user['username']}")
        st.write(f"**Email:** {current_user['email']}")
        st.write(f"**Plano:** {subscription['name']} (R$ {subscription['price']:.2f}/mês)")
    
    with col2:
        if subscription['start_date']:
            # Converte datetime para string se necessário
            start_date = subscription['start_date']
            if hasattr(start_date, 'strftime'):
                start_date_str = start_date.strftime('%Y-%m-%d')
            else:
                start_date_str = str(start_date)[:10]
            st.write(f"**Assinatura desde:** {start_date_str}")
        
        features = subscription['features']
        if features:
            st.write("**Funcionalidades:**")
            for feature in features:
                st.write(f"• {feature}")
    
    # Histórico de uso
    st.divider()
    st.subheader("📈 Uso da Conta")
    
    # Simulação de dados de uso (pode ser expandido)
    st.info(f"📊 Você fez {daily_usage} consultas hoje")
    
    if subscription['priority_support']:
        st.success("🌟 Você tem acesso ao suporte prioritário!")
    else:
        st.info("💡 Faça upgrade para ter suporte prioritário")

def change_plan(user_id: str, plan_id: str):
    """Altera plano do usuário"""
    
    # Simula dados de pagamento
    payment_data = {
        'method': 'upgrade',
        'timestamp': str(st.session_state.get('timestamp', 'now')),
        'user_id': user_id
    }
    
    success = SubscriptionSystem.change_user_plan(user_id, plan_id, payment_data)
    
    if success:
        # Busca dados do novo plano
        plans = SubscriptionSystem.get_available_plans()
        new_plan = next((p for p in plans if p['id'] == plan_id), None)
        
        if new_plan:
            if plan_id == 'free':
                st.success(f"✅ Plano alterado para {new_plan['name']} com sucesso!")
            else:
                st.success(f"🎉 Upgrade realizado! Bem-vindo ao plano {new_plan['name']}!")
                st.balloons()
        
        # Atualiza a página
        st.rerun()
    else:
        st.error("❌ Erro ao alterar plano. Tente novamente.")

# Função principal para renderizar na página
def main():
    """Função principal da página de pagamentos"""
    render_payment_ui()

if __name__ == "__main__":
    main()