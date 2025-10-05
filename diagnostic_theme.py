# ARQUIVO REMOVIDO - teste desnecessário

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Diagnóstico Tema",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Diagnóstico do Seletor de Tema")

# Informações de debug
st.markdown("### 📊 Estado Atual do Session State")
st.json(dict(st.session_state))

# Importa as funções do tema
try:
    from deepseek_theme import render_theme_selector, apply_selected_theme
    st.success("✅ Módulo deepseek_theme importado com sucesso")
except Exception as e:
    st.error(f"❌ Erro ao importar deepseek_theme: {e}")
    st.stop()

# Testa o seletor
st.markdown("### 🎨 Teste do Seletor")

# Estado antes do seletor
st.write("**Estado ANTES do seletor:**")
current_state = dict(st.session_state)
st.json(current_state)

# Renderiza o seletor
selected_theme = render_theme_selector()

# Estado depois do seletor
st.write("**Estado DEPOIS do seletor:**")
new_state = dict(st.session_state)
st.json(new_state)

# Compara estados
st.write("**Mudanças detectadas:**")
changes = {}
for key in set(list(current_state.keys()) + list(new_state.keys())):
    old_val = current_state.get(key, "N/A")
    new_val = new_state.get(key, "N/A")
    if old_val != new_val:
        changes[key] = {"antes": old_val, "depois": new_val}

if changes:
    st.json(changes)
else:
    st.write("Nenhuma mudança detectada")

# Mostra o tema selecionado
st.markdown(f"### 🎯 Tema Selecionado: `{selected_theme}`")

# Testa a aplicação do tema
st.markdown("### 🔧 Teste de Aplicação")
try:
    apply_selected_theme(selected_theme)
    st.success(f"✅ Tema {selected_theme} aplicado com sucesso")
except Exception as e:
    st.error(f"❌ Erro ao aplicar tema: {e}")

# Simulação de mudança de tema
st.markdown("### 🔄 Simulação de Mudança")

# Valor anterior
previous = st.session_state.get('diagnostic_previous', selected_theme)
st.write(f"Tema anterior: `{previous}`")
st.write(f"Tema atual: `{selected_theme}`")

if previous != selected_theme:
    st.warning(f"🔄 MUDANÇA DETECTADA: {previous} → {selected_theme}")
    st.session_state.diagnostic_previous = selected_theme
    
    # Simula o que deveria acontecer no main.py
    if st.button("🔄 Simular st.rerun()"):
        st.rerun()
else:
    st.info("✅ Nenhuma mudança de tema detectada")
    st.session_state.diagnostic_previous = selected_theme

# Teste visual
st.markdown("### 👁️ Teste Visual")
if selected_theme == "claro":
    st.markdown("""
    <div style="background: white; color: black; padding: 20px; border-radius: 10px; border: 1px solid #ccc;">
        ☀️ <strong>TEMA CLARO ATIVO</strong><br>
        Este texto deveria estar preto em fundo branco
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: #0a0a0a; color: white; padding: 20px; border-radius: 10px; border: 1px solid #333;">
        🌙 <strong>TEMA ESCURO ATIVO</strong><br>
        Este texto deveria estar branco em fundo preto
    </div>
    """, unsafe_allow_html=True)

# Instruções finais
st.markdown("### 📝 Instruções")
st.markdown("""
1. **Teste o seletor** no sidebar
2. **Observe as mudanças** no Session State
3. **Verifique se a detecção** funciona
4. **Teste o botão de rerun** se houver mudança
5. **Observe o estilo visual** aplicado
""")

# Botão de reset
if st.button("🔄 Reset Session State"):
    for key in list(st.session_state.keys()):
        if key.startswith(('theme', 'diagnostic', 'previous')):
            del st.session_state[key]
    st.rerun()