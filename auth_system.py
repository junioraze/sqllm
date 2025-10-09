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
    """Renderiza sistema de autenticação"""
    
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
    
    # Título com tema integrado
    st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h1 style="
                background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0066ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                letter-spacing: -0.02em;
            ">ViaQuest</h1>
            <p style="color: rgba(229, 231, 235, 0.7); font-size: 1.1rem;">
                Sistema de Análise de Dados Inteligente
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # MODO EMPRESARIAL: Apenas tela de login, sem cadastro
    if is_empresarial_mode():
        st.subheader("🔑 Login Empresarial")
        render_login_form()
    else:
        # MODO NORMAL: Tabs para Login e Registro
        if st.session_state.get('redirect_to_login', False):
            st.session_state['redirect_to_login'] = False
            default_tab = 0  # Login tab
            st.success("🎉 Conta criada! Faça login com suas credenciais:")
        else:
            default_tab = 0
        
        tab1, tab2 = st.tabs(["🔑 Login", "👤 Criar Conta"])
        
        with tab1:
            render_login_form()
        
        with tab2:
            render_register_form()
    
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