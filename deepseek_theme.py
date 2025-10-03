# DeepSeek Style UI - Tema Escuro Minimalista

DEEPSEEK_DARK_THEME = """
<style>
/* ========================================
   DEEPSEEK DARK THEME - MINIMALISTA
   ======================================== */

/* RESET E BASE - FORÇA ESCURO EM TUDO */
.stApp, .main, [data-testid="stAppViewContainer"], .block-container {
    background: #0a0a0a !important;
    color: #e5e7eb !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}

/* FORÇA FUNDO ESCURO EM TODOS OS ELEMENTOS */
.stApp *, .main *, [data-testid="stAppViewContainer"] *, .block-container * {
    background-color: transparent !important;
    color: #e5e7eb !important;
}

/* CONTAINER PRINCIPAL */
.block-container {
    background: rgba(10, 10, 10, 0.98) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    padding: 2rem !important;
    margin: 1rem !important;
    transition: all 0.3s ease !important;
}

/* OCULTA ELEMENTOS STREAMLIT DESNECESSÁRIOS */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
[data-testid="stStatusWidget"], 
.stMainMenu, 
button[title="View fullscreen"], 
button[data-testid="baseButton-headerNoPadding"], 
[data-testid="stSidebar"],
header[data-testid="stHeader"],
.stAppDeployButton,
#stDecoration {
    display: none !important;
}

/* ========================================
   TÍTULO PRINCIPAL - ESTILO DEEPSEEK
   ======================================== */
h1 {
    background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0066ff 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    margin-bottom: 2rem !important;
    letter-spacing: -0.025em !important;
    animation: titleGlow 3s ease-in-out infinite alternate !important;
}

@keyframes titleGlow {
    0% { filter: brightness(1) drop-shadow(0 0 10px rgba(0, 212, 255, 0.3)); }
    100% { filter: brightness(1.1) drop-shadow(0 0 20px rgba(0, 212, 255, 0.5)); }
}

/* ========================================
   ÁREA DE CHAT - ESTILO DEEPSEEK
   ======================================== */
[data-testid="stChatMessageContainer"] {
    margin-bottom: 1rem !important;
}

.stChatMessage {
    background: rgba(20, 20, 20, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
    animation: messageSlideIn 0.5s ease-out !important;
}

.stChatMessage:hover {
    border-color: rgba(0, 212, 255, 0.3) !important;
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}

@keyframes messageSlideIn {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* MENSAGENS DO USUÁRIO */
[data-testid="chat-message-user"] {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 168, 204, 0.15) 100%) !important;
    border-left: 3px solid #00d4ff !important;
}

[data-testid="chat-message-user"] *,
[data-testid="chat-message-user"] p,
[data-testid="chat-message-user"] div,
[data-testid="chat-message-user"] span {
    color: #e5e7eb !important;
}

/* MENSAGENS DO ASSISTENTE */
[data-testid="chat-message-assistant"] {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%) !important;
    border-left: 3px solid #22c55e !important;
}

[data-testid="chat-message-assistant"] *,
[data-testid="chat-message-assistant"] p,
[data-testid="chat-message-assistant"] div,
[data-testid="chat-message-assistant"] span {
    color: #e5e7eb !important;
}

/* ========================================
   INPUT DE CHAT - ESTILO DEEPSEEK
   ======================================== */
.stChatInput {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 999 !important;
    background: rgba(10, 10, 10, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    padding: 1rem 0 !important;
    margin-top: 2rem !important;
}

.stChatInput > div {
    background: rgba(25, 25, 25, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
    position: relative !important;
    overflow: hidden !important;
}

.stChatInput > div::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: -100% !important;
    width: 100% !important;
    height: 100% !important;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent) !important;
    transition: left 0.6s ease !important;
}

.stChatInput > div:focus-within::before {
    left: 100% !important;
}

.stChatInput > div:focus-within {
    border-color: #00d4ff !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
    transform: scale(1.02) !important;
}

.stChatInput textarea {
    background: transparent !important;
    color: #e5e7eb !important;
    border: none !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    padding: 1rem 1.25rem !important;
    resize: none !important;
    font-family: inherit !important;
}

.stChatInput textarea::placeholder {
    color: rgba(229, 231, 235, 0.5) !important;
    font-style: italic !important;
}

.stChatInput textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* BOTÃO DE ENVIO */
.stChatInput button {
    background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
}

.stChatInput button:hover {
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
}

/* ========================================
   INDICADOR DE TYPING - ANIMAÇÃO
   ======================================== */
.typing-indicator {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 1rem !important;
    background: rgba(25, 25, 25, 0.8) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    margin: 1rem 0 !important;
}

.typing-dots {
    display: flex !important;
    gap: 4px !important;
}

.typing-dot {
    width: 8px !important;
    height: 8px !important;
    background: #00d4ff !important;
    border-radius: 50% !important;
    animation: typingDot 1.5s ease-in-out infinite !important;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s !important; }
.typing-dot:nth-child(3) { animation-delay: 0.4s !important; }

@keyframes typingDot {
    0%, 60%, 100% { transform: scale(1); opacity: 0.5; }
    30% { transform: scale(1.2); opacity: 1; }
}

/* ========================================
   EXPANSORES (DETALHES TÉCNICOS)
   ======================================== */
.stExpander {
    background: rgba(20, 20, 20, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

.stExpander:hover {
    border-color: rgba(0, 212, 255, 0.3) !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.1) !important;
}

.streamlit-expanderHeader {
    background: transparent !important;
    color: #00d4ff !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(0, 212, 255, 0.05) !important;
}

.streamlit-expanderContent {
    background: rgba(15, 15, 15, 0.8) !important;
    color: #e5e7eb !important;
    padding: 1rem !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* ========================================
   BOTÕES DE DOWNLOAD
   ======================================== */
.download-button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.75rem 1.5rem !important;
    margin: 0.5rem !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3) !important;
}

.download-button:hover {
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: 0 6px 25px rgba(34, 197, 94, 0.5) !important;
    text-decoration: none !important;
    color: white !important;
}

/* ========================================
   GRÁFICOS PLOTLY
   ======================================== */
.js-plotly-plot {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(20, 20, 20, 0.8) !important;
    backdrop-filter: blur(10px) !important;
    overflow: hidden !important;
    margin: 1rem 0 !important;
}

/* ========================================
   SCROLLBAR PERSONALIZADA
   ======================================== */
::-webkit-scrollbar {
    width: 8px !important;
}

::-webkit-scrollbar-track {
    background: rgba(20, 20, 20, 0.5) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%) !important;
    border-radius: 4px !important;
    transition: all 0.3s ease !important;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #00a8cc 0%, #0052cc 100%) !important;
}

/* ========================================
   ANIMAÇÕES GLOBAIS
   ======================================== */
.main {
    animation: pageLoad 0.8s ease-out !important;
}

@keyframes pageLoad {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* ========================================
   RESPONSIVIDADE MOBILE
   ======================================== */
@media screen and (max-width: 768px) {
    .block-container {
        margin: 0.5rem !important;
        padding: 1rem !important;
        border-radius: 12px !important;
    }
    
    h1 {
        font-size: 2rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    .stChatMessage {
        padding: 1rem !important;
    }
    
    .stChatInput {
        padding: 0.75rem 0 !important;
    }
}

/* ========================================
   LOGIN SCREEN - DEEPSEEK STYLE (SIMPLIFICADO)
   ======================================== */

/* INPUT FIELDS NO LOGIN */
.stTextInput input,
.stPasswordInput input {
    background: rgba(25, 25, 25, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 8px !important;
    color: #e5e7eb !important;
    padding: 0.75rem !important;
}

.stTextInput input:focus,
.stPasswordInput input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
}

/* BOTÕES NO LOGIN */
.stButton button {
    background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4) !important;
}

/* LABELS NO LOGIN */
.stTextInput label,
.stPasswordInput label {
    color: #e5e7eb !important;
    font-weight: 500 !important;
    margin-bottom: 0.5rem !important;
}

/* ======================================== */


.deepseek-glow {
    position: relative !important;
}

.deepseek-glow::before {
    content: '' !important;
    position: absolute !important;
    top: -2px !important;
    left: -2px !important;
    right: -2px !important;
    bottom: -2px !important;
    background: linear-gradient(45deg, #00d4ff, #0066ff, #22c55e, #00d4ff) !important;
    border-radius: inherit !important;
    z-index: -1 !important;
    opacity: 0 !important;
    transition: opacity 0.3s ease !important;
    background-size: 300% 300% !important;
    animation: gradientShift 3s ease infinite !important;
}

.deepseek-glow:hover::before {
    opacity: 0.7 !important;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ========================================
   LOADER PERSONALIZADO
   ======================================== */
.deepseek-loader {
    display: inline-flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 1rem !important;
    background: rgba(25, 25, 25, 0.9) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
    backdrop-filter: blur(10px) !important;
}

.deepseek-spinner {
    width: 20px !important;
    height: 20px !important;
    border: 2px solid rgba(0, 212, 255, 0.3) !important;
    border-top: 2px solid #00d4ff !important;
    border-radius: 50% !important;
    animation: spin 1s linear infinite !important;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ========================================
   HIGHLIGHTING ESPECIAL PARA IA
   ======================================== */
.ia-highlight {
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-weight: 700 !important;
    filter: drop-shadow(0 0 8px rgba(255, 107, 53, 0.5)) !important;
    animation: iaGlow 2s ease-in-out infinite alternate !important;
}

@keyframes iaGlow {
    0% { filter: drop-shadow(0 0 8px rgba(255, 107, 53, 0.3)); }
    100% { filter: drop-shadow(0 0 15px rgba(255, 107, 53, 0.7)); }
}

/* ========================================
   INDICADOR DE USO/RATE LIMIT
   ======================================== */
.usage-indicator {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: rgba(20, 20, 20, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    backdrop-filter: blur(10px) !important;
    font-size: 0.875rem !important;
    color: #e5e7eb !important;
    z-index: 1000 !important;
    transition: all 0.3s ease !important;
}

.usage-indicator:hover {
    background: rgba(25, 25, 25, 0.95) !important;
    border-color: rgba(0, 212, 255, 0.3) !important;
}

</style>
"""

# Função para aplicar o tema
def apply_deepseek_theme():
    """Aplica o tema escuro estilo DeepSeek"""
    additional_css = """
    <style>
    /* FORÇA ESCURO EM ELEMENTOS ESPECÍFICOS - ANTI-WHITE BACKGROUND */
    div[data-testid="stSidebar"] {
        background: rgba(10, 10, 10, 0.95) !important;
    }

    /* FORÇA ESCURO EM TOOLBARS E HEADERS */
    header[data-testid="stHeader"],
    .stToolbar,
    .streamlit-expanderHeader,
    .stAlert,
    .stSuccess,
    .stInfo,
    .stWarning,
    .stError {
        background: rgba(15, 15, 15, 0.9) !important;
        color: #e5e7eb !important;
    }

    /* FORÇA ESCURO EM SELECTBOX E WIDGETS */
    .stSelectbox > div,
    .stMultiSelect > div,
    .stDateInput > div,
    .stTimeInput > div,
    .stNumberInput > div {
        background: rgba(25, 25, 25, 0.9) !important;
    }

    /* FORÇA ESCURO EM DROPDOWNS */
    .stSelectbox [data-baseweb="select"],
    .stSelectbox [data-testid="stSelectbox"] {
        background: rgba(25, 25, 25, 0.9) !important;
        color: #e5e7eb !important;
    }

    /* FORÇA ESCURO EM ELEMENTOS DE FORMULÁRIO */
    .stForm {
        background: rgba(15, 15, 15, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* FORÇA ESCURO EM PLACEHOLDERS */
    .stEmpty,
    .stPlaceholder {
        background: transparent !important;
    }

    /* FORÇA TEXTO BRANCO EM TODOS OS ELEMENTOS DE TEXTO */
    p, span, div, h1, h2, h3, h4, h5, h6, label, li, td, th {
        color: #e5e7eb !important;
    }

    /* EXCEÇÕES PARA LINKS E ELEMENTOS COLORIDOS */
    a {
        color: #00d4ff !important;
    }

    a:hover {
        color: #00a8cc !important;
    }
    </style>
    """
    
    return DEEPSEEK_DARK_THEME + additional_css

# Função para aplicar tema na tela de login (sem mostrar código)
def get_login_theme():
    """Retorna o CSS para a tela de login"""
    return """
    <style>
    /* OCULTA ELEMENTOS STREAMLIT DESNECESSÁRIOS NO LOGIN */
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], 
    .stMainMenu, 
    button[title="View fullscreen"], 
    button[data-testid="baseButton-headerNoPadding"], 
    [data-testid="stSidebar"],
    header[data-testid="stHeader"],
    .stAppDeployButton,
    #stDecoration {
        display: none !important;
    }
    
    /* TEMA ESCURO BASE */
    .stApp, .main, [data-testid="stAppViewContainer"], .block-container {
        background: #0a0a0a !important;
        color: #e5e7eb !important;
    }
    
    /* INPUTS DE LOGIN */
    .stTextInput input, .stPasswordInput input {
        background: rgba(25, 25, 25, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #e5e7eb !important;
        padding: 0.75rem !important;
    }
    .stTextInput input:focus, .stPasswordInput input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }
    
    /* BOTÃO DE LOGIN */
    .stButton button {
        background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4) !important;
    }
    
    /* LABELS E TEXTOS */
    .stTextInput label, .stPasswordInput label {
        color: #e5e7eb !important;
        font-weight: 500 !important;
    }
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #e5e7eb !important;
    }
    </style>
    """

# Função para aplicar tema no chat (sem mostrar código)
def get_chat_theme():
    """Retorna o CSS para a tela do chat - VERSÃO LIMPA"""
    css_content = """
    <style>
    /* DEEPSEEK DARK THEME - APLICADO SILENCIOSAMENTE */
    .stApp, .main, [data-testid="stAppViewContainer"], .block-container {
        background: #0a0a0a !important;
        color: #e5e7eb !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }

    .stApp *, .main *, [data-testid="stAppViewContainer"] *, .block-container * {
        background-color: transparent !important;
        color: #e5e7eb !important;
    }

    .block-container {
        background: rgba(10, 10, 10, 0.98) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        padding: 2rem !important;
        margin: 1rem !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], 
    .stMainMenu, 
    button[title="View fullscreen"], 
    button[data-testid="baseButton-headerNoPadding"], 
    [data-testid="stSidebar"],
    header[data-testid="stHeader"],
    .stAppDeployButton,
    #stDecoration {
        display: none !important;
    }

    h1 {
        background: linear-gradient(135deg, #e5e7eb 0%, #f9fafb 50%, #e5e7eb 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin: 2rem 0 !important;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) !important;
    }

    .stChatInput {
        position: fixed !important;
        bottom: 2rem !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 4rem) !important;
        max-width: 800px !important;
        z-index: 100 !important;
        background: rgba(20, 20, 20, 0.95) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        padding: 1rem !important;
    }

    .stChatInput textarea {
        background: transparent !important;
        border: none !important;
        color: #e5e7eb !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        resize: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    .stChatInput textarea::placeholder {
        color: rgba(229, 231, 235, 0.6) !important;
        font-style: italic !important;
    }

    .stChatMessage {
        background: rgba(25, 25, 25, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        margin: 1rem 0 !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        animation: messageSlideIn 0.5s ease-out !important;
    }

    .stChatMessage:hover {
        border-color: rgba(0, 212, 255, 0.3) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1) !important;
    }

    [data-testid="chat-message-user"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 168, 204, 0.15) 100%) !important;
        border-left: 3px solid #00d4ff !important;
    }

    [data-testid="chat-message-assistant"] {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%) !important;
        border-left: 3px solid #22c55e !important;
    }

    /* FORÇA ESCURO EM ELEMENTOS ESPECÍFICOS */
    div[data-testid="stSidebar"],
    header[data-testid="stHeader"],
    .stToolbar,
    .streamlit-expanderHeader,
    .stAlert,
    .stSuccess,
    .stInfo,
    .stWarning,
    .stError,
    .stSelectbox > div,
    .stMultiSelect > div,
    .stForm {
        background: rgba(15, 15, 15, 0.9) !important;
        color: #e5e7eb !important;
    }

    p, span, div, h1, h2, h3, h4, h5, h6, label, li, td, th {
        color: #e5e7eb !important;
    }

    a {
        color: #00d4ff !important;
    }

    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """
    
    return css_content

# Script para efeitos JavaScript
DEEPSEEK_JS = """
<script>
// DEEPSEEK TYPING ANIMATION
function showTypingIndicator() {
    const chatContainer = document.querySelector('[data-testid="stChatMessageContainer"]');
    if (chatContainer) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <span style="color: #00d4ff; font-weight: 600;">IA está pensando</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
    }
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// ANIMAÇÃO DE ENTRADA PARA NOVOS ELEMENTOS
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1 && node.classList && node.classList.contains('stChatMessage')) {
                node.style.animation = 'messageSlideIn 0.5s ease-out';
            }
        });
    });
});

// INICIA OBSERVAÇÃO
document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.querySelector('[data-testid="stChatMessageContainer"]');
    if (chatContainer) {
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
});

// EFEITO DE GLOW NOS BOTÕES
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button, .download-button');
    buttons.forEach(button => {
        button.classList.add('deepseek-glow');
    });
});

// SMOOTH SCROLL PARA NOVAS MENSAGENS
function scrollToBottom() {
    const chatContainer = document.querySelector('.main');
    if (chatContainer) {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// AUTO-SCROLL QUANDO NOVA MENSAGEM APARECE
const chatObserver = new MutationObserver(() => {
    setTimeout(scrollToBottom, 100);
});

document.addEventListener('DOMContentLoaded', () => {
    const main = document.querySelector('.main');
    if (main) {
        chatObserver.observe(main, { childList: true, subtree: true });
    }
});
</script>
"""

# Função para indicador de typing
def show_typing_animation():
    """Mostra animação de typing sutil e integrada"""
    return """
    <div style="
        padding: 8px 12px;
        color: #00d4ff;
        font-size: 14px;
        font-weight: 500;
        opacity: 0.8;
        display: flex;
        align-items: center;
        gap: 8px;
    ">
        <span class="typing-dots">Analisando</span>
        <span class="dots-animation">...</span>
    </div>
    
    <style>
    .dots-animation {
        animation: blink 1.5s linear infinite;
    }
    @keyframes blink {
        0%, 20% { opacity: 0; }
        40%, 60% { opacity: 0.5; }
        80%, 100% { opacity: 1; }
    }
    .typing-dots {
        animation: subtle-glow 2s ease-in-out infinite alternate;
    }
    @keyframes subtle-glow {
        from { opacity: 0.6; }
        to { opacity: 1; }
    }
    </style>
    """

# Função para indicador de uso
def create_usage_indicator(current_usage, max_usage):
    """Cria indicador de uso no estilo DeepSeek"""
    percentage = (current_usage / max_usage) * 100
    color = "#22c55e" if percentage < 70 else "#f59e0b" if percentage < 90 else "#ef4444"
    
    return f"""
    <div class="usage-indicator">
        <span style="color: {color};">Uso: {current_usage}/{max_usage}</span>
        <div style="width: 60px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 4px;">
            <div style="width: {percentage}%; height: 100%; background: {color}; border-radius: 2px; transition: all 0.3s ease;"></div>
        </div>
    </div>
    """