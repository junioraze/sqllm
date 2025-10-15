#!/usr/bin/env python3
"""Sistema de autenticação com registro de usuários"""

import streamlit as st
import re
import json
import os
from typing import Tuple, Dict, Optional
from user_database import db
from deepseek_theme import get_login_theme, get_enhanced_cards_theme, get_expert_login_theme
from config import is_empresarial_mode

class AuthSystem:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Valida força da senha"""
        if len(password) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        if not re.search(r'[A-Za-z]', password):
            return False, "Senha deve conter pelo menos uma letra"
        if not re.search(r'[0-9]', password):
            return False, "Senha deve conter pelo menos um número"
        return True, "Senha válida"

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Valida username"""
        if len(username) < 3:
            return False, "Nome de usuário deve ter pelo menos 3 caracteres"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Nome de usuário deve conter apenas letras, números, _ ou -"
        return True, "Nome de usuário válido"

def setup_empresarial_plan(user_id):
    """Configura plano empresarial com limite de 100 consultas"""
    try:
        # Verifica se plano empresarial já existe
        plans = db.get_available_plans()
        empresarial_plan = None
        for plan in plans:
            if plan['plan_id'] == 'empresarial':
                empresarial_plan = plan
                break
        
        # Se não existe, cria o plano empresarial
        if not empresarial_plan:
            db.create_plan(
                plan_id='empresarial',
                name='Empresarial',
                description='Plano empresarial com 100 consultas diárias',
                price=0,
                daily_limit=100,
                features='["100 consultas por dia", "Acesso completo", "Interface simplificada"]',
                priority_support=True
            )
            print("✅ Plano empresarial criado")
        
        # Atribui plano empresarial ao usuário
        db.assign_plan_to_user(user_id, 'empresarial')
        print(f"✅ Plano empresarial atribuído ao usuário {user_id}")
        
    except Exception as e:
        print(f"❌ Erro ao configurar plano empresarial: {e}")

def ensure_empresarial_user():
    """Garante que o usuário empresarial existe (mas não faz login automático)"""
    if not is_empresarial_mode():
        return
        
    try:
        with open("credentials.json", "r", encoding="utf-8") as f:
            credentials = json.load(f)
        
        email = credentials.get("login", "admin@empresa.com")
        password = credentials.get("password", "123456")
        
        # Verifica se usuário já existe
        existing_user = db.get_user_by_email(email)
        if not existing_user:
            # Cria usuário empresarial
            username = email.split("@")[0]  # Usa parte do email como username
            success, result = db.create_user(username, email, password)
            if success:
                # Busca o usuário criado para obter o ID
                created_user = db.get_user_by_email(email)
                if created_user:
                    print(f"✅ Usuário empresarial criado: {email}")
                    # Cria e atribui plano empresarial com limite de 100
                    setup_empresarial_plan(created_user['id'])
            else:
                print(f"❌ Erro ao criar usuário: {result}")
        else:
            # Verifica se já tem plano empresarial
            subscription = db.get_user_subscription(existing_user['id'])
            if not subscription or subscription['plan_id'] != 'empresarial':
                setup_empresarial_plan(existing_user['id'])
        
    except Exception as e:
        print(f"❌ Erro ao configurar usuário empresarial: {e}")

def render_auth_system():
    """Renderiza sistema de autenticação em layout otimizado"""
    
    # Garante que usuário empresarial existe (se estiver no modo empresarial)
    ensure_empresarial_user()
    
    # Se já está autenticado, não mostra tela de login
    if st.session_state.get('authenticated', False):
        return True
    
    # Aplica tema de login especialista e cards melhorados
    st.markdown(get_expert_login_theme(), unsafe_allow_html=True)
    st.markdown(get_enhanced_cards_theme(), unsafe_allow_html=True)
    
    # CORREÇÃO: Aplica cores de input específica para data-baseweb="input"
    from deepseek_theme import fix_baseweb_input_dark_theme
    fix_baseweb_input_dark_theme()
    
    # CSS para o novo layout 1-1 + 222
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0.5rem !important;
    }
    .stColumns, .stColumns > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px !important;
    }
    .stForm {
        margin-bottom: 0.5rem !important;
    }
    .stAlert {
        margin-bottom: 0.5rem !important;
        padding: 0.75rem !important;
    }
    /* Alinhar altura dos blocos de login */
    .login-align-stretch {
        height: 220px;
        min-height: 180px;
        display: flex;
        align-items: stretch;
        justify-content: center;
        padding: 0 !important;
        margin: 0 !important;
    }
    .login-align-stretch-inner {
        flex: 1;
        display: flex;
        align-items: stretch;
        justify-content: center;
        background: rgba(0, 212, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 0 !important;
        margin: 0 !important;
        height: 100%;
    }
    .login-logo-img {
        object-fit: contain;
        height: 100%;
        width: 100%;
        margin: 0 !important;
        padding: 0 !important;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Conteúdo principal - NOVO LAYOUT 1-1 + 222
    if is_empresarial_mode():
        # MODO EMPRESARIAL - Layout 1-1 + 222
        col1, col2 = st.columns(2)
        with col1:
            from image_utils import get_base64_image
            logo_path = os.path.join(os.path.dirname(__file__), "etc", "desc_logo.jpg")
            logo_b64 = get_base64_image(logo_path)
            if logo_b64:
                logo_html = f"<img src='data:image/jpeg;base64,{logo_b64}' alt='ViaQuest' class='login-logo-img'/>"
            else:
                logo_html = (
                    "<h3 style=\"background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0066ff 100%);"
                    "-webkit-background-clip: text;-webkit-text-fill-color: transparent;background-clip: text;"
                    "font-size: 1.8rem;font-weight: 700;margin: 0;text-align: center;display: flex;align-items: center;"
                    "justify-content: center;height: 100%;\">ViaQuest</h3>"
                )
            st.markdown(
                f"""
                <div class='login-align-stretch'>
                  <div class='login-align-stretch-inner'>
                    {logo_html}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown("""
                <div class='login-align-stretch'>
                  <div class='login-align-stretch-inner'>
                    <div style='width:100%;display:flex;flex-direction:column;justify-content:center;'>
                      <h4 style='color: #00d4ff; margin-bottom: 0.8rem; text-align: center;'>🏢 Acesso Corporativo</h4>
                      <p style='margin: 0.3rem 0; font-size: 0.9rem; text-align: center;'><strong>Recursos Inclusos</strong></p>
                      <p style='margin: 0.2rem 0; font-size: 0.85rem; text-align: center;'>• 100 consultas diárias<br>• Acesso completo<br>• Suporte prioritário</p>
                    </div>
                  </div>
                </div>
            """, unsafe_allow_html=True)
        # Linha 222 - Formulário ocupando largura total
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        st.subheader("🔑 Login Corporativo", anchor=False)
        render_login_form_compact()
    
    else:
        # MODO NORMAL - Layout similar
        col1, col2 = st.columns(2)
        
        with col1:
            # Coluna 1 - Logo (mesma altura do quadro)
            from image_utils import get_base64_image
            logo_path = os.path.join(os.path.dirname(__file__), "etc", "desc_logo.jpg")
            logo_b64 = get_base64_image(logo_path)
            
            if logo_b64:
                st.markdown(f"""
                    <div style='
                        background: rgba(0, 212, 255, 0.05); 
                        padding: 1.2rem; 
                        border-radius: 10px; 
                        border: 1px solid rgba(0, 212, 255, 0.2);
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    '>
                        <img src='data:image/jpeg;base64,{logo_b64}' alt='ViaQuest' style='max-width:160px; width:100%; height:auto;'/>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='
                        background: rgba(0, 212, 255, 0.05); 
                        padding: 1.2rem; 
                        border-radius: 10px; 
                        border: 1px solid rgba(0, 212, 255, 0.2);
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    '>
                        <h3 style="
                            background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0066ff 100%);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                            font-size: 1.8rem;
                            font-weight: 700;
                            margin: 0;
                            text-align: center;
                        ">ViaQuest</h3>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Coluna 2 - Vantagens
            st.markdown("""
                <div style='
                    background: rgba(0, 212, 255, 0.05); 
                    padding: 1.2rem; 
                    border-radius: 10px; 
                    border: 1px solid rgba(0, 212, 255, 0.2);
                    height: 100%;
                '>
                <h4 style='color: #00d4ff; margin-bottom: 0.8rem; text-align: center;'>🚀 Vantagens</h4>
                <p style='margin: 0.3rem 0; font-size: 0.9rem; text-align: center;'><strong>Recursos</strong></p>
                <p style='margin: 0.2rem 0; font-size: 0.85rem; text-align: center;'>• Consultas por IA<br>• Gráficos interativos<br>• Exportação de dados</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Linha 222 - Tabs ocupando largura total
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        
        if st.session_state.get('redirect_to_login', False):
            st.session_state['redirect_to_login'] = False
            st.success("🎉 Conta criada! Faça login:", icon="✅")
        
        tab1, tab2 = st.tabs(["**🔑 Login**", "**👤 Registrar**"])
        
        with tab1:
            render_login_form_compact()
        
        with tab2:
            render_register_form_compact()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False

def render_login_form():
    """Formulário de login"""
    st.subheader("Fazer Login")
    
    with st.form("login_form"):
        username = st.text_input("Nome de usuário ou Email:", placeholder="Digite seu nome de usuário ou email")
        password = st.text_input("Senha:", type="password", placeholder="Digite sua senha")
        submit_login = st.form_submit_button("🔑 Entrar", use_container_width=True)
        
        if submit_login:
            if not username or not password:
                st.error("❌ Por favor, preencha todos os campos")
                return
            
            # Autentica usuário
            success, user_data = db.authenticate_user(username, password)
            
            if success:
                # Configura sessão
                st.session_state.authenticated = True
                st.session_state.user_id = user_data['id']
                st.session_state.username = user_data['username']
                st.session_state.user_email = user_data['email']
                
                st.success(f"✅ Bem-vindo, {user_data['username']}!")
                st.rerun()
            else:
                st.error("❌ Nome de usuário/email ou senha incorretos")

def render_register_form():
    """Formulário de registro"""
    st.subheader("Criar Nova Conta")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Nome de usuário:", placeholder="Ex: joao123")
            email = st.text_input("Email:", placeholder="seu@email.com")
        
        with col2:
            password = st.text_input("Senha:", type="password", placeholder="Mínimo 6 caracteres")
            confirm_password = st.text_input("Confirmar senha:", type="password", placeholder="Digite a senha novamente")
        
        # Mostra planos disponíveis
        st.markdown("### 📋 Planos Disponíveis")
        plans = db.get_available_plans()
        
        for plan in plans:
            with st.expander(f"{plan['name']} - R$ {plan['price']:.2f}/mês"):
                st.write(f"**{plan['description']}**")
                features = eval(plan['features']) if plan['features'] else []
                for feature in features:
                    st.write(f"• {feature}")
        
        submit_register = st.form_submit_button("👤 Criar Conta", use_container_width=True)
        
        if submit_register:
            # Validações
            if not all([username, email, password, confirm_password]):
                st.error("❌ Por favor, preencha todos os campos")
                return
            
            if password != confirm_password:
                st.error("❌ As senhas não conferem")
                return
            
            # Valida email
            if not AuthSystem.validate_email(email):
                st.error("❌ Formato de email inválido")
                return
            
            # Valida username
            valid_username, username_msg = AuthSystem.validate_username(username)
            if not valid_username:
                st.error(f"❌ {username_msg}")
                return
            
            # Valida senha
            valid_password, password_msg = AuthSystem.validate_password(password)
            if not valid_password:
                st.error(f"❌ {password_msg}")
                return
            
            # Cria usuário
            success, message = db.create_user(username, email, password)
            
            if success:
                st.success("🎉 Conta criada com sucesso!")
                st.session_state['redirect_to_login'] = True
                st.rerun()
            else:
                st.error(f"❌ {message}")

def get_current_user() -> Optional[Dict]:
    """Retorna dados do usuário atual"""
    if not st.session_state.get('authenticated', False):
        return None
    
    return {
        'id': st.session_state.get('user_id'),
        'username': st.session_state.get('username'),
        'email': st.session_state.get('user_email')
    }

def logout_user():
    """Faz logout do usuário"""
    for key in ['authenticated', 'user_id', 'username', 'user_email', 'current_user']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def require_auth():
    """Decorator para funções que precisam de autenticação"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False):
                st.error("❌ Você precisa estar logado para acessar esta funcionalidade")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def render_login_form_compact():
    """Formulário de login compacto para tela única"""
    with st.form("login_form_compact", clear_on_submit=False):
        username = st.text_input(
            "**Usuário ou Email**",
            placeholder="Digite seu usuário ou email",
            key="login_username_compact"
        )
        password = st.text_input(
            "**Senha**", 
            type="password", 
            placeholder="Sua senha",
            key="login_password_compact"
        )
        
        submit_login = st.form_submit_button(
            "**🔑 Entrar**", 
            use_container_width=True,
            type="primary"
        )
        
        if submit_login:
            if not username or not password:
                st.error("❌ Preencha todos os campos")
                return
            
            success, user_data = db.authenticate_user(username, password)
            
            if success:
                st.session_state.authenticated = True
                st.session_state.user_id = user_data['id']
                st.session_state.username = user_data['username']
                st.session_state.user_email = user_data['email']
                
                st.success(f"✅ Bem-vindo, {user_data['username']}!")
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas")

def render_register_form_compact():
    """Formulário de registro compacto para tela única"""
    with st.form("register_form_compact", clear_on_submit=False):
        username = st.text_input(
            "**Nome de usuário**", 
            placeholder="Escolha um nome de usuário",
            key="reg_username_compact"
        )
        email = st.text_input(
            "**Email**", 
            placeholder="seu@email.com",
            key="reg_email_compact"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input(
                "**Senha**", 
                type="password", 
                placeholder="Senha",
                key="reg_password_compact"
            )
        with col2:
            confirm_password = st.text_input(
                "**Confirmar**", 
                type="password", 
                placeholder="Confirmar",
                key="reg_confirm_compact"
            )
        
        st.markdown("""
        <div style='
            background: rgba(0, 212, 255, 0.1); 
            padding: 0.6rem; 
            border-radius: 6px; 
            border: 1px solid rgba(0, 212, 255, 0.3);
            margin: 0.3rem 0;
            font-size: 0.8rem;
        '>
        <strong>🎯 Plano Grátis</strong> - 10 consultas/dia
        </div>
        """, unsafe_allow_html=True)
        
        submit_register = st.form_submit_button(
            "**👤 Criar Conta Grátis**", 
            use_container_width=True,
            type="primary"
        )
        
        if submit_register:
            if not all([username, email, password, confirm_password]):
                st.error("❌ Preencha todos os campos")
                return
            
            if password != confirm_password:
                st.error("❌ Senhas não conferem")
                return
            
            if not AuthSystem.validate_email(email):
                st.error("❌ Email inválido")
                return
            
            valid_username, username_msg = AuthSystem.validate_username(username)
            if not valid_username:
                st.error(f"❌ {username_msg}")
                return
            
            valid_password, password_msg = AuthSystem.validate_password(password)
            if not valid_password:
                st.error(f"❌ {password_msg}")
                return
            
            success, message = db.create_user(username, email, password)
            
            if success:
                st.success("🎉 Conta criada! Faça login.")
                st.session_state['redirect_to_login'] = True
                st.rerun()
            else:
                st.error(f"❌ {message}")