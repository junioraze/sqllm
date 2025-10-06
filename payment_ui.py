#!/usr/bin/env python3
"""Interface de Pagamento - Mesmo Layout do Chat"""
import streamlit as st
from payment_handler import get_available_plans, create_payment_preference

def check_user_subscription(email):
    """Verifica status de assinatura usando sistema integrado"""
    if not email:
        return "free"
    
    # Importa apenas quando necessário para evitar ciclo
    from subscription_manager import get_user_subscription_info
    subscription_info = get_user_subscription_info()
    
    return subscription_info.get('status', 'free')

def render_payment_page():
    """Página de pagamentos com largura forçada total"""
    
    # CSS para forçar largura total e tamanhos menores
    st.markdown("""
    <style>
    /* FORÇA LARGURA TOTAL DA PÁGINA - SOBRESCREVE TUDO */
    .stApp {
        max-width: 100vw !important;
        width: 100vw !important;
    }
    
    .main {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    .main .block-container {
        max-width: none !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* SOBRESCREVE O DEEPSEEK THEME */
    [data-testid="stAppViewContainer"] .main .block-container {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* FORÇA LARGURA DAS TABS */
    [data-testid="stTabs"] {
        width: 100% !important;
    }
    
    [data-testid="stTabContent"] {
        width: 100% !important;
        max-width: none !important;
    }
    
    /* REDUZ TAMANHO DAS MÉTRICAS */
    [data-testid="metric-container"] {
        background: rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 0.5rem !important;
        border-radius: 8px !important;
        min-height: auto !important;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: rgba(255, 255, 255, 0.7) !important;
        white-space: nowrap !important;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-size: 0.6rem !important;
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* REDUZ TAMANHO DOS BOTÕES */
    .stButton > button {
        height: 2rem !important;
        font-size: 0.75rem !important;
        padding: 0.25rem 0.5rem !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
    }
    
    /* REMOVE MARGENS DESNECESSÁRIAS */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    /* FORÇA COLUNAS A OCUPAREM ESPAÇO TOTAL */
    [data-testid="column"] {
        width: 100% !important;
        max-width: none !important;
        flex: 1 !important;
    }
    
    /* FORÇA RADIO BUTTONS A NÃO LIMITAREM */
    [data-testid="stRadio"] {
        width: 100% !important;
    }
    
    /* REMOVE LIMITAÇÕES DE CONTAINERS INTERNOS */
    .stContainer {
        width: 100% !important;
        max-width: none !important;
    }
    
    /* DEBUG: FORÇA TUDO A SER VERDE PARA VER LARGURA REAL */
    .main, .main .block-container {
        border: 2px solid lime !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal SEM TABS - largura total
    st.title("💳 Planos e Assinaturas")
    st.subheader("Escolha o plano ideal para suas necessidades")
    
    # Navegação simples sem tabs limitantes
    page_option = st.radio("Seção:", ["💎 Planos Disponíveis", "👤 Minha Conta"], horizontal=True, key="payment_nav", label_visibility="collapsed")
    
    if page_option == "💎 Planos Disponíveis":
        render_plans_section()
    else:
        render_subscription_section()

def render_plans_section():
    """Seção de planos SEM COLUNAS - largura total real"""
    
    plans = get_available_plans()
    
    st.markdown("### 🚀 Nossos Planos")
    st.write("Soluções profissionais para análise de dados")
    
    # TESTE: Renderiza cada plano SEM COLUNAS
    for i, plan in enumerate(plans):
        
        # Linha divisória entre planos
        if i > 0:
            st.markdown("---")
            
        # Destaque para plano popular
        if plan.get('highlight'):
            st.success("🏆 MAIS POPULAR")
        
        # Título do plano
        st.markdown(f"### {plan['name']}")
        
        # TUDO EM LINHA ÚNICA SEM COLUNAS - TESTE
        st.write(f"💰 **R$ {plan['price']:.0f}/mês** | 📊 **{plan['query_limit']} consultas/dia** | 🎧 **Suporte {'VIP' if plan.get('priority_support') else 'Email'}**")
        
        # Descrição compacta
        st.caption(f"**{plan['description']}**")
        
        # Features em linha
        features_text = " • ".join(plan['features'])
        st.caption(f"✅ {features_text}")
        
        # Botão sem coluna
        button_type = "primary" if plan.get('highlight') else "secondary"
        if st.button(
            f"🚀 Contratar {plan['name']}", 
            key=f"btn_plan_{plan['id']}", 
            type=button_type,
            use_container_width=False  # TESTE: sem usar largura total
        ):
            handle_plan_selection(plan)

def render_subscription_section():
    """Seção de conta usando componentes nativos Streamlit"""
    
    user_email = st.session_state.get('user_email', '')
    
    # Usa sistema integrado para obter informações completas
    from subscription_manager import get_user_subscription_info, get_daily_usage_session
    
    subscription_info = get_user_subscription_info()
    
    st.markdown("### 👤 Status da Conta")
    
    # Status atual usando dados reais
    plan_type = subscription_info.get('status', 'free')
    if plan_type != 'free':
        st.success(f"✅ **{subscription_info['description']}** - Sua assinatura está ativa")
        
        # Métricas da conta ativa com dados reais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", "Ativo", "✅")
        
        with col2:
            # Usa dados reais do session_state
            queries_today = get_daily_usage_session(user_email) if user_email else 0
            st.metric("Consultas Hoje", queries_today)
        
        with col3:
            st.metric("Limite Diário", subscription_info['daily_limit'])
        
        with col4:
            remaining = subscription_info['daily_limit'] - queries_today
            st.metric("Disponível", remaining)
        
        # Progress bar com dados reais
        progress_percentage = min(queries_today / subscription_info['daily_limit'], 1.0)
        st.progress(progress_percentage, text=f"Uso diário: {queries_today}/{subscription_info['daily_limit']} consultas")
        
        # Funcionalidades do plano
        st.markdown("#### 🎯 Recursos do Seu Plano")
        features_text = " • ".join(subscription_info.get('features', []))
        st.info(f"✅ {features_text}")
        
    else:
        st.info("🆓 **Conta Gratuita** - Faça upgrade para desbloquear recursos premium")
        
        # Métricas da conta gratuita
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", "Gratuito", "🆓")
        
        with col2:
            queries_today = st.session_state.get('queries_today', 0)
            st.metric("Consultas Hoje", queries_today)
        
        with col3:
            st.metric("Limite Diário", "10")
        
        with col4:
            remaining = 10 - queries_today
            st.metric("Disponível", remaining)
        
        # Progress bar para conta gratuita
        progress_percentage = min(queries_today / 10, 1.0)
        st.progress(progress_percentage, text=f"Uso diário: {queries_today}/10 consultas")
        
        # Call to action
        st.divider()
        st.markdown("#### 🚀 Upgrade Recomendado")
        st.write("💡 **Dica:** Planos premium oferecem até 10x mais consultas e recursos avançados")
        
        if st.button("⭐ Fazer Upgrade", type="primary", use_container_width=True):
            st.rerun()

def handle_plan_selection(plan):
    """Processa seleção de plano"""
    user_email = st.session_state.get('user_email', '')
    
    if not user_email:
        st.error("❌ Erro: Usuário não autenticado")
        return
    
    # Simula ativação com spinner nativo
    with st.spinner(f"Ativando {plan['name']}..."):
        from payment_handler import simulate_successful_payment
        
        try:
            result = simulate_successful_payment(user_email, plan['id'])
            
            if result['status'] == 'approved':
                st.success(f"🎉 **{plan['name']}** ativado com sucesso!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Erro ao processar pagamento")
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

def check_feature_access_ui(feature_name: str) -> bool:
    """Verifica acesso a features"""
    user_email = st.session_state.get('user_email', '')
    subscription_status = check_user_subscription(user_email)
    
    if subscription_status == 'active':
        return True
    else:
        st.warning(f"⚠️ **{feature_name}** disponível apenas nos planos premium")
        return False