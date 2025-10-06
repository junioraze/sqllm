import streamlit as st

# ========================================
# TEMA ESCURO - CSS VARIABLES
# ========================================
DEEPSEEK_DARK_THEME = """
<style>
/* VARIÁVEIS DE COR - TEMA ESCURO */
:root {
    --bg-primary: #0a0a0a;
    --bg-secondary: rgba(10, 10, 10, 0.98);
    --bg-tertiary: rgba(20, 20, 20, 0.8);
    --bg-input: rgba(25, 25, 25, 0.9);
    --bg-sidebar: linear-gradient(180deg, #0f0f0f 0%, #1a1a1a 100%);
    --bg-chat-input: rgba(10, 10, 10, 0.95);
    --bg-typing: rgba(25, 25, 25, 0.8);
    --bg-usage: rgba(20, 20, 20, 0.9);
    --bg-usage-hover: rgba(25, 25, 25, 0.95);
    
    --text-primary: #e5e7eb;
    --text-secondary: rgba(229, 231, 235, 0.5);
    --text-accent: #00d4ff;
    
    --border-primary: rgba(255, 255, 255, 0.1);
    --border-secondary: rgba(255, 255, 255, 0.2);
    --border-accent: #00d4ff;
    --border-hover: rgba(0, 212, 255, 0.3);
    
    --shadow-primary: 0 8px 32px rgba(0, 0, 0, 0.5);
    --shadow-hover: 0 4px 20px rgba(0, 212, 255, 0.1);
    --shadow-focus: 0 0 20px rgba(0, 212, 255, 0.3);
    --shadow-button: 0 4px 15px rgba(0, 212, 255, 0.3);
    --shadow-button-hover: 0 6px 25px rgba(0, 212, 255, 0.5);
    
    --gradient-title: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0099ff 100%);
    --gradient-button: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-download: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-user: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 168, 204, 0.15) 100%);
    --gradient-assistant: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
    --gradient-shimmer: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    --gradient-scrollbar: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-scrollbar-hover: linear-gradient(135deg, #00a8cc 0%, #0088cc 100%);
}

/* ESTRUTURA BASE ÚNICA */
.stApp, .main, [data-testid="stAppViewContainer"], .block-container {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}

.stApp *, .main *, [data-testid="stAppViewContainer"] *, .block-container * {
    background-color: transparent !important;
    color: var(--text-primary) !important;
}

/* CONTAINER PRINCIPAL */
.block-container {
    background: var(--bg-secondary) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-primary) !important;
    box-shadow: var(--shadow-primary) !important;
    padding: 2rem !important;
    margin: 1rem !important;
    transition: all 0.3s ease !important;
    max-width: none !important;
    width: auto !important;
}

/* OCULTA ELEMENTOS STREAMLIT - FUNCIONA EM TODOS OS TEMAS */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
[data-testid="stStatusWidget"], 
.stMainMenu, 
button[title="View fullscreen"], 
button[data-testid="baseButton-headerNoPadding"], 
header[data-testid="stHeader"],
.stAppDeployButton,
#stDecoration {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-primary) !important;
    display: block !important;
}

section[data-testid="stSidebar"] h3 {
    color: var(--text-accent) !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] .stRadio > div > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

section[data-testid="stSidebar"] .stRadio > div > div > label {
    color: var(--text-primary) !important;
}

section[data-testid="stSidebar"] .stRadio > div > div:hover {
    border-color: var(--border-hover) !important;
    background: rgba(0, 212, 255, 0.05) !important;
}

/* RADIO BUTTONS - ESTRUTURA ÚNICA */
.stSidebar div[data-testid="stRadio"] input[type="radio"] {
    background-color: #ffffff !important;
    border: 3px solid var(--border-accent) !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    accent-color: var(--border-accent) !important;
    -webkit-appearance: none !important;
    appearance: none !important;
    position: relative !important;
}

.stSidebar div[data-testid="stRadio"] input[type="radio"]:checked {
    background-color: var(--border-accent) !important;
    border-color: var(--border-accent) !important;
}

.stSidebar div[data-testid="stRadio"] input[type="radio"]:checked::after {
    content: '' !important;
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
}

/* TÍTULO PRINCIPAL */
h1 {
    background: var(--gradient-title) !important;
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

/* ÁREA DE CHAT */
[data-testid="stChatMessageContainer"] {
    margin-bottom: 1rem !important;
}

.stChatMessage {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
    animation: messageSlideIn 0.5s ease-out !important;
}

.stChatMessage:hover {
    border-color: var(--border-hover) !important;
    box-shadow: var(--shadow-hover) !important;
    transform: translateY(-2px) !important;
}

@keyframes messageSlideIn {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* MENSAGENS DO USUÁRIO */
[data-testid="chat-message-user"] {
    background: var(--gradient-user) !important;
    border-left: 3px solid var(--text-accent) !important;
}

[data-testid="chat-message-user"] *,
[data-testid="chat-message-user"] p,
[data-testid="chat-message-user"] div,
[data-testid="chat-message-user"] span {
    color: var(--text-primary) !important;
}

/* MENSAGENS DO ASSISTENTE */
[data-testid="chat-message-assistant"] {
    background: var(--gradient-assistant) !important;
    border-left: 3px solid #22c55e !important;
}

[data-testid="chat-message-assistant"] *,
[data-testid="chat-message-assistant"] p,
[data-testid="chat-message-assistant"] div,
[data-testid="chat-message-assistant"] span {
    color: var(--text-primary) !important;
}

/* INPUT DE CHAT */
.stChatInput {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 999 !important;
    background: var(--bg-chat-input) !important;
    backdrop-filter: blur(20px) !important;
    padding: 1rem 0 !important;
    margin-top: 2rem !important;
}

.stChatInput > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
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
    background: var(--gradient-shimmer) !important;
    transition: left 0.6s ease !important;
}

.stChatInput > div:focus-within::before {
    left: 100% !important;
}

.stChatInput > div:focus-within {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-focus) !important;
    transform: scale(1.02) !important;
}

.stChatInput textarea {
    background: transparent !important;
    color: var(--text-primary) !important;
    border: none !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    padding: 1rem 1.25rem !important;
    resize: none !important;
    font-family: inherit !important;
    caret-color: var(--text-accent) !important;
}

.stChatInput textarea::placeholder {
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

.stChatInput textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* BOTÃO DE ENVIO */
.stChatInput button {
    background: var(--gradient-button) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-button) !important;
}

.stChatInput button:hover {
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: var(--shadow-button-hover) !important;
}

/* BOTÕES GERAIS */
.stButton button {
    background: var(--gradient-button) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-button) !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-button-hover) !important;
}

/* INPUTS DE TEXTO */
.stTextInput input,
.stPasswordInput input,
.stTextInput textarea, 
.stTextArea textarea, 
input[type="text"], 
input[type="password"], 
input[type="email"] {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    padding: 1rem 1.25rem !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    caret-color: var(--text-accent) !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px) !important;
}

.stTextInput input:focus,
.stPasswordInput input:focus,
.stTextInput textarea:focus, 
.stTextArea textarea:focus, 
input[type="text"]:focus, 
input[type="password"]:focus, 
input[type="email"]:focus {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-focus) !important;
    transform: scale(1.02) !important;
    outline: none !important;
}

.stTextInput input::placeholder,
.stPasswordInput input::placeholder,
.stTextInput textarea::placeholder, 
.stTextArea textarea::placeholder, 
input::placeholder {
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

/* LABELS */
.stTextInput label,
.stPasswordInput label {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    margin-bottom: 0.5rem !important;
}

/* TYPING INDICATOR */
.typing-indicator {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 1rem !important;
    background: var(--bg-typing) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-primary) !important;
    margin: 1rem 0 !important;
}

.typing-dots {
    display: flex !important;
    gap: 4px !important;
}

.typing-dot {
    width: 8px !important;
    height: 8px !important;
    background: var(--text-accent) !important;
    border-radius: 50% !important;
    animation: typingDot 1.5s ease-in-out infinite !important;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s !important; }
.typing-dot:nth-child(3) { animation-delay: 0.4s !important; }

@keyframes typingDot {
    0%, 60%, 100% { transform: scale(1); opacity: 0.5; }
    30% { transform: scale(1.2); opacity: 1; }
}

/* EXPANSORES */
.stExpander {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

.stExpander:hover {
    border-color: var(--border-hover) !important;
    box-shadow: var(--shadow-hover) !important;
}

.streamlit-expanderHeader {
    background: transparent !important;
    color: var(--text-accent) !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(0, 212, 255, 0.05) !important;
}

.streamlit-expanderContent {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    padding: 1rem !important;
    border-top: 1px solid var(--border-primary) !important;
}

/* BOTÕES DE DOWNLOAD */
.download-button {
    background: var(--gradient-download) !important;
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

/* DATAFRAMES E GRÁFICOS */

.stDataFrame {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
}

/* Estilização específica para container Streamlit Plotly - TEMA ESCURO */
.stPlotlyChart {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-hover) !important;
    margin: 1rem 0 !important;
    overflow: hidden !important;
    padding: 0.5rem !important;
    transition: all 0.3s ease !important;
}

.stPlotlyChart:hover {
    border-color: var(--border-hover) !important;
    box-shadow: var(--shadow-primary) !important;
    transform: translateY(-1px) !important;
}

/* Garantir que o gráfico interno mantenha o tema escuro */
.stPlotlyChart > div,
.stPlotlyChart .plotly-graph-div {
    background: var(--bg-tertiary) !important;
    border-radius: 8px !important;
}

/* Estilização da barra de ferramentas do Plotly */
.stPlotlyChart .modebar {
    background: rgba(15, 15, 23, 0.9) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 6px !important;
}

.stPlotlyChart .modebar-btn {
    color: var(--text-primary) !important;
}

.stPlotlyChart .modebar-btn:hover {
    background: rgba(0, 212, 255, 0.1) !important;
    color: var(--text-accent) !important;
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 8px !important;
}

::-webkit-scrollbar-track {
    background: var(--bg-tertiary) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb {
    background: var(--gradient-scrollbar) !important;
    border-radius: 4px !important;
    transition: all 0.3s ease !important;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--gradient-scrollbar-hover) !important;
}

/* ANIMAÇÕES GLOBAIS */
.main {
    animation: pageLoad 0.8s ease-out !important;
}

@keyframes pageLoad {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* RESPONSIVIDADE MOBILE */
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

/* HIGHLIGHTING ESPECIAL PARA IA */
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

/* INDICADOR DE USO */
.usage-indicator {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: var(--bg-usage) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    backdrop-filter: blur(10px) !important;
    font-size: 0.875rem !important;
    color: var(--text-primary) !important;
    z-index: 1000 !important;
    transition: all 0.3s ease !important;
}

.usage-indicator:hover {
    background: var(--bg-usage-hover) !important;
    border-color: var(--border-hover) !important;
}

/* DYNAMIC PROCESSING INDICATOR */
.typing-indicator.dynamic-processing {
    background: linear-gradient(135deg, var(--bg-typing) 0%, rgba(0, 212, 255, 0.05) 100%) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.1) !important;
    animation: processGlow 2s ease-in-out infinite alternate !important;
}

@keyframes processGlow {
    0% { 
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.1);
        border-color: rgba(0, 212, 255, 0.2);
    }
    100% { 
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.3);
        border-color: rgba(0, 212, 255, 0.4);
    }
}

</style>
"""

# ========================================
# TEMA CLARO - CSS VARIABLES
# ========================================
DEEPSEEK_LIGHT_THEME = """
<style>
/* VARIÁVEIS DE COR - TEMA CLARO */
:root {
    --bg-primary: #f8fafc;
    --bg-secondary: rgba(255, 255, 255, 0.98);
    --bg-tertiary: rgba(255, 255, 255, 0.8);
    --bg-input: rgba(255, 255, 255, 0.9);
    --bg-sidebar: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    --bg-chat-input: rgba(248, 250, 252, 0.95);
    --bg-typing: rgba(255, 255, 255, 0.8);
    --bg-usage: rgba(255, 255, 255, 0.9);
    --bg-usage-hover: rgba(248, 250, 252, 0.95);
    
    --text-primary: #334155;
    --text-secondary: rgba(51, 65, 85, 0.5);
    --text-accent: #0ea5e9;
    
    --border-primary: rgba(0, 0, 0, 0.1);
    --border-secondary: rgba(0, 0, 0, 0.2);
    --border-accent: #0ea5e9;
    --border-hover: rgba(14, 165, 233, 0.3);
    
    --shadow-primary: 0 8px 32px rgba(0, 0, 0, 0.1);
    --shadow-hover: 0 4px 20px rgba(14, 165, 233, 0.1);
    --shadow-focus: 0 0 20px rgba(0, 212, 255, 0.3);
    --shadow-button: 0 4px 15px rgba(0, 212, 255, 0.3);
    --shadow-button-hover: 0 6px 25px rgba(0, 212, 255, 0.5);
    
    --gradient-title: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0099ff 100%);
    --gradient-button: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-download: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-user: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 168, 204, 0.1) 100%);
    --gradient-assistant: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
    --gradient-shimmer: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    --gradient-scrollbar: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    --gradient-scrollbar-hover: linear-gradient(135deg, #00a8cc 0%, #0088cc 100%);
}

/* ESTRUTURA BASE ÚNICA */
.stApp, .main, [data-testid="stAppViewContainer"], .block-container {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}

.stApp *, .main *, [data-testid="stAppViewContainer"] *, .block-container * {
    background-color: transparent !important;
    color: var(--text-primary) !important;
}

/* CONTAINER PRINCIPAL */
.block-container {
    background: var(--bg-secondary) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-primary) !important;
    box-shadow: var(--shadow-primary) !important;
    padding: 2rem !important;
    margin: 1rem !important;
    transition: all 0.3s ease !important;
    max-width: none !important;
    width: auto !important;
}

/* OCULTA ELEMENTOS STREAMLIT - FUNCIONA EM TODOS OS TEMAS */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
[data-testid="stStatusWidget"], 
.stMainMenu, 
button[title="View fullscreen"], 
button[data-testid="baseButton-headerNoPadding"], 
header[data-testid="stHeader"],
.stAppDeployButton,
#stDecoration {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-primary) !important;
    display: block !important;
}

section[data-testid="stSidebar"] h3 {
    color: var(--text-accent) !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] .stRadio > div > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

section[data-testid="stSidebar"] .stRadio > div > div > label {
    color: var(--text-primary) !important;
}

section[data-testid="stSidebar"] .stRadio > div > div:hover {
    border-color: var(--border-hover) !important;
    background: rgba(14, 165, 233, 0.05) !important;
}

/* RADIO BUTTONS - ESTRUTURA ÚNICA */
.stSidebar div[data-testid="stRadio"] input[type="radio"] {
    background-color: #ffffff !important;
    border: 3px solid var(--border-accent) !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    accent-color: var(--border-accent) !important;
    -webkit-appearance: none !important;
    appearance: none !important;
    position: relative !important;
}

.stSidebar div[data-testid="stRadio"] input[type="radio"]:checked {
    background-color: var(--border-accent) !important;
    border-color: var(--border-accent) !important;
}

.stSidebar div[data-testid="stRadio"] input[type="radio"]:checked::after {
    content: '' !important;
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
}

/* TÍTULO PRINCIPAL */
h1 {
    background: var(--gradient-title) !important;
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
    0% { filter: brightness(1) drop-shadow(0 0 10px rgba(14, 165, 233, 0.3)); }
    100% { filter: brightness(1.1) drop-shadow(0 0 20px rgba(14, 165, 233, 0.5)); }
}

/* ÁREA DE CHAT */
[data-testid="stChatMessageContainer"] {
    margin-bottom: 1rem !important;
}

.stChatMessage {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
    animation: messageSlideIn 0.5s ease-out !important;
}

.stChatMessage:hover {
    border-color: var(--border-hover) !important;
    box-shadow: var(--shadow-hover) !important;
    transform: translateY(-2px) !important;
}

@keyframes messageSlideIn {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* MENSAGENS DO USUÁRIO */
[data-testid="chat-message-user"] {
    background: var(--gradient-user) !important;
    border-left: 3px solid var(--text-accent) !important;
}

[data-testid="chat-message-user"] *,
[data-testid="chat-message-user"] p,
[data-testid="chat-message-user"] div,
[data-testid="chat-message-user"] span {
    color: var(--text-primary) !important;
}

/* MENSAGENS DO ASSISTENTE */
[data-testid="chat-message-assistant"] {
    background: var(--gradient-assistant) !important;
    border-left: 3px solid #22c55e !important;
}

[data-testid="chat-message-assistant"] *,
[data-testid="chat-message-assistant"] p,
[data-testid="chat-message-assistant"] div,
[data-testid="chat-message-assistant"] span {
    color: var(--text-primary) !important;
}

/* INPUT DE CHAT */
.stChatInput {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 999 !important;
    background: var(--bg-chat-input) !important;
    backdrop-filter: blur(20px) !important;
    padding: 1rem 0 !important;
    margin-top: 2rem !important;
}

.stChatInput > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
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
    background: var(--gradient-shimmer) !important;
    transition: left 0.6s ease !important;
}

.stChatInput > div:focus-within::before {
    left: 100% !important;
}

.stChatInput > div:focus-within {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-focus) !important;
    transform: scale(1.02) !important;
}

.stChatInput textarea {
    background: transparent !important;
    color: var(--text-primary) !important;
    border: none !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    padding: 1rem 1.25rem !important;
    resize: none !important;
    font-family: inherit !important;
    caret-color: var(--text-accent) !important;
}

.stChatInput textarea::placeholder {
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

.stChatInput textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* BOTÃO DE ENVIO */
.stChatInput button {
    background: var(--gradient-button) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-button) !important;
}

.stChatInput button:hover {
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: var(--shadow-button-hover) !important;
}

/* BOTÕES GERAIS */
.stButton button {
    background: var(--gradient-button) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-button) !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-button-hover) !important;
}

/* INPUTS DE TEXTO */
.stTextInput input,
.stPasswordInput input,
.stTextInput textarea, 
.stTextArea textarea, 
input[type="text"], 
input[type="password"], 
input[type="email"] {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-secondary) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    padding: 1rem 1.25rem !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    caret-color: var(--text-accent) !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px) !important;
}

.stTextInput input:focus,
.stPasswordInput input:focus,
.stTextInput textarea:focus, 
.stTextArea textarea:focus, 
input[type="text"]:focus, 
input[type="password"]:focus, 
input[type="email"]:focus {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-focus) !important;
    transform: scale(1.02) !important;
    outline: none !important;
}

.stTextInput input::placeholder,
.stPasswordInput input::placeholder,
.stTextInput textarea::placeholder, 
.stTextArea textarea::placeholder, 
input::placeholder {
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

/* LABELS */
.stTextInput label,
.stPasswordInput label {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    margin-bottom: 0.5rem !important;
}

/* TYPING INDICATOR */
.typing-indicator {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 1rem !important;
    background: var(--bg-typing) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-primary) !important;
    margin: 1rem 0 !important;
}

.typing-dots {
    display: flex !important;
    gap: 4px !important;
}

.typing-dot {
    width: 8px !important;
    height: 8px !important;
    background: var(--text-accent) !important;
    border-radius: 50% !important;
    animation: typingDot 1.5s ease-in-out infinite !important;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s !important; }
.typing-dot:nth-child(3) { animation-delay: 0.4s !important; }

@keyframes typingDot {
    0%, 60%, 100% { transform: scale(1); opacity: 0.5; }
    30% { transform: scale(1.2); opacity: 1; }
}

/* EXPANSORES */
.stExpander {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s ease !important;
}

.stExpander:hover {
    border-color: var(--border-hover) !important;
    box-shadow: var(--shadow-hover) !important;
}

.streamlit-expanderHeader {
    background: transparent !important;
    color: var(--text-accent) !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(14, 165, 233, 0.05) !important;
}

.streamlit-expanderContent {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    padding: 1rem !important;
    border-top: 1px solid var(--border-primary) !important;
}

/* BOTÕES DE DOWNLOAD */
.download-button {
    background: var(--gradient-download) !important;
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

/* DATAFRAMES E GRÁFICOS */

.stDataFrame {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 12px !important;
}

/* Estilização específica para container Streamlit Plotly - TEMA CLARO */
.stPlotlyChart {
    background: #ffffff !important;
    border: 1px solid rgba(209, 213, 219, 0.6) !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    margin: 1rem 0 !important;
    overflow: hidden !important;
    padding: 0.5rem !important;
    transition: all 0.3s ease !important;
}

.stPlotlyChart:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.10) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* Garantir que o gráfico interno tenha fundo completamente branco */
.stPlotlyChart > div,
.stPlotlyChart .plotly-graph-div,
.stPlotlyChart .svg-container,
.stPlotlyChart .plot-container {
    background: #ffffff !important;
    border-radius: 8px !important;
}

/* Forçar cores escuras nos textos dos gráficos para contraste */
.stPlotlyChart .plotly-graph-div text {
    fill: #1f2937 !important;
    color: #1f2937 !important;
}

/* Estilização da barra de ferramentas do Plotly */
.stPlotlyChart .modebar {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(209, 213, 219, 0.4) !important;
    border-radius: 6px !important;
}

.stPlotlyChart .modebar-btn {
    color: #374151 !important;
}

.stPlotlyChart .modebar-btn:hover {
    background: rgba(59, 130, 246, 0.1) !important;
    color: #1d4ed8 !important;
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 8px !important;
}

::-webkit-scrollbar-track {
    background: var(--bg-tertiary) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb {
    background: var(--gradient-scrollbar) !important;
    border-radius: 4px !important;
    transition: all 0.3s ease !important;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--gradient-scrollbar-hover) !important;
}

/* ANIMAÇÕES GLOBAIS */
.main {
    animation: pageLoad 0.8s ease-out !important;
}

@keyframes pageLoad {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* RESPONSIVIDADE MOBILE */
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

/* HIGHLIGHTING ESPECIAL PARA IA */
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

/* INDICADOR DE USO */
.usage-indicator {
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: var(--bg-usage) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    backdrop-filter: blur(10px) !important;
    font-size: 0.875rem !important;
    color: var(--text-primary) !important;
    z-index: 1000 !important;
    transition: all 0.3s ease !important;
}

.usage-indicator:hover {
    background: var(--bg-usage-hover) !important;
    border-color: var(--border-hover) !important;
}

</style>
"""

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def get_login_theme():
    """Retorna o CSS completo para a tela de login/registro integrado ao tema"""
    return """
    <style>
    /* VARIÁVEIS DE COR - TEMA ESCURO INTEGRADO */
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: rgba(10, 10, 10, 0.98);
        --bg-tertiary: rgba(20, 20, 20, 0.8);
        --bg-input: rgba(25, 25, 25, 0.9);
        --text-primary: #e5e7eb;
        --text-secondary: rgba(229, 231, 235, 0.5);
        --text-accent: #00d4ff;
        --border-primary: rgba(255, 255, 255, 0.1);
        --border-secondary: rgba(255, 255, 255, 0.2);
        --border-accent: #00d4ff;
        --shadow-focus: 0 0 20px rgba(0, 212, 255, 0.3);
        --gradient-button: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
        --success-bg: rgba(0, 212, 255, 0.15);
        --success-border: #00d4ff;
        --success-text: #00d4ff;
        --error-bg: rgba(239, 68, 68, 0.15);
        --error-border: #ef4444;
        --error-text: #ff6b6b;
        --warning-bg: rgba(245, 158, 11, 0.15);
        --warning-border: #f59e0b;
        --warning-text: #fbbf24;
        --info-bg: rgba(0, 212, 255, 0.2);
        --info-border: #00d4ff;
        --info-text: #00d4ff;
    }

    /* BASE LOGIN THEME */
    .stApp, .main, [data-testid="stAppViewContainer"], .block-container {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }
    
    /* OCULTA ELEMENTOS STREAMLIT */
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], 
    .stMainMenu, 
    button[title="View fullscreen"], 
    button[data-testid="baseButton-headerNoPadding"], 
    header[data-testid="stHeader"],
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .stAppDeployButton,
    #stDecoration {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* CONTAINER PRINCIPAL */
    .block-container {
        background: var(--bg-secondary) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--border-primary) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        padding: 2rem !important;
        margin: 1rem !important;
        max-width: 800px !important;
        animation: fadeIn 0.8s ease-out !important;
    }

    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* TABS DO STREAMLIT */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-tertiary) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        border: 1px solid var(--border-primary) !important;
        margin-bottom: 2rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 212, 255, 0.1) !important;
        color: var(--text-accent) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--gradient-button) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }

    /* INPUTS DE LOGIN/REGISTRO */
    .stTextInput input, 
    .stPasswordInput input,
    .stTextInput input[type="email"] {
        background: var(--bg-input) !important;
        border: 1px solid var(--border-secondary) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    .stTextInput input::placeholder, 
    .stPasswordInput input::placeholder {
        color: var(--text-secondary) !important;
        font-style: italic !important;
    }

    .stTextInput label, 
    .stPasswordInput label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    .stTextInput input:focus, 
    .stPasswordInput input:focus {
        border-color: var(--border-accent) !important;
        box-shadow: var(--shadow-focus) !important;
        transform: scale(1.02) !important;
        outline: none !important;
    }

    /* BOTÕES DE LOGIN/REGISTRO */
    .stButton button {
        background: var(--gradient-button) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
        font-size: 1rem !important;
    }

    .stButton button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
    }

    /* ALERTAS DE SUCESSO */
    .stAlert[data-baseweb="notification"] {
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        border-width: 1px !important;
        border-style: solid !important;
        padding: 1rem 1.25rem !important;
        margin: 1rem 0 !important;
    }

    /* Sucesso - Verde */
    .stSuccess, [data-testid="stAlert"][data-baseweb="notification"]:has([data-testid="successIcon"]) {
        background: var(--success-bg) !important;
        border-color: var(--success-border) !important;
        color: var(--success-text) !important;
    }

    .stSuccess [data-testid="successIcon"], 
    [data-testid="stAlert"] [data-testid="successIcon"] {
        color: var(--success-text) !important;
    }

    /* Erro - Vermelho */
    .stError, [data-testid="stAlert"][data-baseweb="notification"]:has([data-testid="errorIcon"]) {
        background: var(--error-bg) !important;
        border-color: var(--error-border) !important;
        color: var(--error-text) !important;
    }

    .stError [data-testid="errorIcon"], 
    [data-testid="stAlert"] [data-testid="errorIcon"] {
        color: var(--error-text) !important;
    }

    /* Warning - Amarelo */
    .stWarning, [data-testid="stAlert"][data-baseweb="notification"]:has([data-testid="warningIcon"]) {
        background: var(--warning-bg) !important;
        border-color: var(--warning-border) !important;
        color: var(--warning-text) !important;
    }

    .stWarning [data-testid="warningIcon"], 
    [data-testid="stAlert"] [data-testid="warningIcon"] {
        color: var(--warning-text) !important;
    }

    /* Info - Azul */
    .stInfo, [data-testid="stAlert"][data-baseweb="notification"]:has([data-testid="infoIcon"]) {
        background: var(--info-bg) !important;
        border-color: var(--info-border) !important;
        color: var(--info-text) !important;
    }

    .stInfo [data-testid="infoIcon"], 
    [data-testid="stAlert"] [data-testid="infoIcon"] {
        color: var(--info-text) !important;
    }

    /* EXPANSORES DE PLANOS */
    .stExpander {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 12px !important;
        margin: 0.5rem 0 !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }

    .stExpander:hover {
        border-color: rgba(0, 212, 255, 0.3) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1) !important;
    }

    .streamlit-expanderHeader {
        background: transparent !important;
        color: var(--text-accent) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(0, 212, 255, 0.05) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        border-top: 1px solid var(--border-primary) !important;
    }

    /* COLUNAS */
    .stColumn {
        padding: 0 0.5rem !important;
    }

    /* FORM CONTAINERS */
    .stForm {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        backdrop-filter: blur(10px) !important;
    }

    /* CARDS INFORMATIVOS - MELHOR CONTRASTE */
    .stAlert, .stMarkdown div[data-testid="stMarkdownContainer"] {
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Cards de Info com ícone 💡 */
    .stInfo, 
    .stMarkdown div:has-text("💡"),
    [data-testid="stMarkdownContainer"]:has(p:contains("💡")),
    div[data-testid="stMarkdownContainer"] p:contains("💡") {
        background: var(--info-bg) !important;
        border: 1px solid var(--info-border) !important;
        color: var(--info-text) !important;
        padding: 1.25rem !important;
        margin: 1rem 0 !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }

    /* MELHORAR TODOS OS BOTÕES */
    .stButton button, 
    button[kind="primary"],
    button[kind="secondary"] {
        background: var(--gradient-button) !important;
        border: 1px solid var(--border-accent) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }

    .stButton button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
        border-color: var(--border-accent) !important;
    }

    /* BOTÕES SECUNDÁRIOS */
    button[kind="secondary"] {
        background: rgba(0, 212, 255, 0.1) !important;
        color: var(--text-accent) !important;
        border: 1px solid var(--border-accent) !important;
    }

    /* TODAS AS BORDAS DE FOCO */
    *:focus,
    *:focus-visible {
        outline: 2px solid var(--border-accent) !important;
        outline-offset: 2px !important;
    }

    /* ANIMAÇÃO DE BALLOONS */
    .balloons {
        animation: celebrate 2s ease-in-out !important;
    }

    @keyframes celebrate {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    </style>
    """

def get_expert_login_theme():
    """Tema de login ESPECIALISTA com gradientes azuis da marca"""
    return """
    <style>
    /* ================================
       TEMA DE LOGIN - MARCA AZUL GRADIENTE
       ================================ */

    /* VARIÁVEIS DA MARCA */
    :root {
        --brand-blue: #00d4ff;
        --brand-blue-dark: #0099ff;
        --brand-gradient: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
        --brand-gradient-hover: linear-gradient(135deg, #00b8e6 0%, #007acc 100%);
        --bg-dark: #0a0a0a;
        --bg-card: rgba(15, 15, 15, 0.95);
        --bg-input: rgba(20, 20, 20, 0.9);
        --text-white: #ffffff;
        --text-gray: rgba(255, 255, 255, 0.7);
        --border-brand: #00d4ff;
        --shadow-brand: 0 8px 32px rgba(0, 212, 255, 0.3);
        --shadow-hover: 0 12px 48px rgba(0, 212, 255, 0.4);
    }

    /* ESTRUTURA BASE */
    .stApp {
        background: var(--bg-dark) !important;
        color: var(--text-white) !important;
    }

    /* OCULTAR ELEMENTOS STREAMLIT */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    .stMainMenu,
    .stAppDeployButton,
    button[title="View fullscreen"] {
        display: none !important;
    }

    /* CONTAINER PRINCIPAL */
    .block-container {
        background: var(--bg-card) !important;
        border: 2px solid var(--border-brand) !important;
        border-radius: 20px !important;
        box-shadow: var(--shadow-brand) !important;
        backdrop-filter: blur(20px) !important;
        max-width: 600px !important;
        padding: 2.5rem !important;
        margin: 2rem auto !important;
    }

    /* ================================
       TABS (ABAS LOGIN/CADASTRO) - CORRIGIDO
       ================================ */
    .stTabs [data-baseweb="tab-list"],
    .stTabs div[role="tablist"] {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 2px solid var(--brand-blue) !important;
        border-radius: 15px !important;
        padding: 8px !important;
        margin-bottom: 2rem !important;
    }

    .stTabs [data-baseweb="tab"],
    .stTabs button[role="tab"] {
        background: transparent !important;
        color: var(--text-gray) !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        margin: 0 4px !important;
    }

    .stTabs [data-baseweb="tab"]:hover,
    .stTabs button[role="tab"]:hover {
        background: rgba(0, 212, 255, 0.2) !important;
        color: var(--brand-blue) !important;
        border-color: var(--brand-blue) !important;
        transform: translateY(-2px) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs button[role="tab"][aria-selected="true"] {
        background: var(--brand-gradient) !important;
        color: var(--text-white) !important;
        border-color: var(--brand-blue) !important;
        box-shadow: var(--shadow-brand) !important;
        transform: translateY(-2px) !important;
    }

    /* ================================
       INPUTS (EMAIL, SENHA, USUÁRIO) - CORRIGIDO
       ================================ */
    
    /* Seletores mais específicos para inputs do Streamlit */
    .stTextInput > div > div > input,
    .stPasswordInput > div > div > input,
    div[data-testid="textInput"] input,
    div[data-testid="passwordInput"] input,
    input[type="text"],
    input[type="email"], 
    input[type="password"] {
        background: var(--bg-input) !important;
        border: 2px solid var(--brand-blue) !important;
        border-radius: 12px !important;
        color: var(--text-white) !important;
        padding: 16px 20px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stPasswordInput > div > div > input::placeholder,
    input::placeholder {
        color: var(--text-gray) !important;
        font-style: italic !important;
    }

    .stTextInput > div > div > input:focus,
    .stPasswordInput > div > div > input:focus,
    input:focus {
        border: 2px solid var(--brand-blue) !important;
        box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.3), inset 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        transform: scale(1.02) !important;
        outline: none !important;
        background: rgba(0, 212, 255, 0.05) !important;
    }

    .stTextInput label,
    .stPasswordInput label,
    label {
        color: var(--brand-blue) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
    }

    /* ================================
       BOTÕES (LOGIN, CADASTRO) - CORRIGIDO
       ================================ */
    
    /* Seletores mais específicos para botões do Streamlit */
    .stButton > button,
    .stFormSubmitButton > button,
    button[kind="primary"],
    button[kind="secondary"],
    div[data-testid="stButton"] button,
    button[type="submit"] {
        background: var(--brand-gradient) !important;
        border: 2px solid var(--brand-blue) !important;
        border-radius: 12px !important;
        color: var(--text-white) !important;
        padding: 16px 32px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-brand) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        cursor: pointer !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    button:hover {
        background: var(--brand-gradient-hover) !important;
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: var(--shadow-hover) !important;
        border-color: var(--brand-blue) !important;
    }

    .stButton > button:active,
    button:active {
        transform: translateY(-1px) scale(0.98) !important;
        background: var(--brand-gradient) !important;
    }

    /* ================================
       ALERTAS E AVISOS MELHORADOS
       ================================ */
    .stAlert {
        border-radius: 12px !important;
        border-width: 2px !important;
        border-style: solid !important;
        padding: 16px 20px !important;
        margin: 16px 0 !important;
        font-weight: 600 !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Sucesso - Azul da marca */
    .stSuccess,
    [data-testid="stAlert"]:has([data-testid="successIcon"]) {
        background: rgba(0, 212, 255, 0.15) !important;
        border-color: var(--brand-blue) !important;
        color: var(--text-white) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2) !important;
    }

    .stSuccess [data-testid="successIcon"],
    [data-testid="stAlert"] [data-testid="successIcon"] {
        color: var(--brand-blue) !important;
    }

    /* Erro - Vermelho claro */
    .stError,
    [data-testid="stAlert"]:has([data-testid="errorIcon"]) {
        background: rgba(255, 107, 107, 0.15) !important;
        border-color: #ff6b6b !important;
        color: var(--text-white) !important;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.2) !important;
    }

    .stError [data-testid="errorIcon"],
    [data-testid="stAlert"] [data-testid="errorIcon"] {
        color: #ff6b6b !important;
    }

    /* Warning - Amarelo */
    .stWarning,
    [data-testid="stAlert"]:has([data-testid="warningIcon"]) {
        background: rgba(255, 193, 7, 0.15) !important;
        border-color: #ffc107 !important;
        color: var(--text-white) !important;
        box-shadow: 0 4px 20px rgba(255, 193, 7, 0.2) !important;
    }

    .stWarning [data-testid="warningIcon"],
    [data-testid="stAlert"] [data-testid="warningIcon"] {
        color: #ffc107 !important;
    }

    /* Info - Azul da marca */
    .stInfo,
    [data-testid="stAlert"]:has([data-testid="infoIcon"]) {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: var(--brand-blue) !important;
        color: var(--text-white) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.25) !important;
    }

    .stInfo [data-testid="infoIcon"],
    [data-testid="stAlert"] [data-testid="infoIcon"] {
        color: var(--brand-blue) !important;
    }

    /* ================================
       CARDS INFORMATIVOS (💡)
       ================================ */
    .element-container:has(p:contains("💡")),
    .stMarkdown:has(p:contains("💡")),
    [data-testid="stMarkdownContainer"]:has(p:contains("💡")),
    div:has(p:contains("💡")) {
        background: rgba(0, 212, 255, 0.15) !important;
        border: 2px solid var(--brand-blue) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 20px 0 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-brand) !important;
        backdrop-filter: blur(15px) !important;
    }

    /* TEXTO DENTRO DOS CARDS INFORMATIVOS */
    .element-container:has(p:contains("💡")) p,
    .stMarkdown:has(p:contains("💡")) p,
    [data-testid="stMarkdownContainer"]:has(p:contains("💡")) p,
    div:has(p:contains("💡")) p {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    }

    /* TEXTO COM EMOJI 💡 ESPECÍFICO */
    p:contains("💡"),
    div p:contains("💡"),
    [data-testid="stMarkdownContainer"] p:contains("💡") {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5) !important;
        background: rgba(0, 212, 255, 0.15) !important;
        border: 2px solid var(--brand-blue) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin: 20px 0 !important;
        box-shadow: var(--shadow-brand) !important;
        backdrop-filter: blur(15px) !important;
    }

    .element-container:has(p:contains("💡")):hover,
    .stMarkdown:has(p:contains("💡")):hover,
    p:contains("💡"):hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-hover) !important;
        background: rgba(0, 212, 255, 0.2) !important;
    }

    /* ================================
       ANIMAÇÕES E EFEITOS
       ================================ */
    @keyframes fadeInUp {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .block-container {
        animation: fadeInUp 0.6s ease-out !important;
    }

    /* Efeito de brilho nos inputs */
    .stTextInput > div > div > input:focus::before,
    .stPasswordInput > div > div > input:focus::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: var(--brand-gradient);
        border-radius: 12px;
        z-index: -1;
        opacity: 0.3;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }

    /* ================================
       RESPONSIVIDADE
       ================================ */
    @media (max-width: 768px) {
        .block-container {
            margin: 1rem !important;
            padding: 1.5rem !important;
        }
        
        .stButton > button {
            padding: 14px 24px !important;
            font-size: 14px !important;
        }
        
        .stTextInput > div > div > input,
        .stPasswordInput > div > div > input {
            padding: 14px 16px !important;
            font-size: 14px !important;
        }
    }
    </style>
    """

def get_enhanced_cards_theme():
    """CSS específico para melhorar a visibilidade dos cards informativos"""
    return """
    <style>
    /* CARDS INFORMATIVOS - SOLUÇÃO ELEGANTE E ESPECÍFICA */
    
    /* Identifica especificamente elementos st.info e similares */
    .stAlert[data-baseweb="notification"],
    div[data-testid="stAlert"] {
        border-radius: 16px !important;
        border-width: 2px !important;
        padding: 1.25rem !important;
        margin: 1.5rem 0 !important;
        backdrop-filter: blur(10px) !important;
        font-weight: 600 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Alertas de informação - Azul da marca */
    .stAlert[data-baseweb="notification"]:has([data-testid="infoIcon"]),
    div[data-testid="stAlert"]:has([data-testid="infoIcon"]),
    .stInfo {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: #00d4ff !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.25) !important;
    }
    
    /* Força branco APENAS nos alertas de info */
    .stAlert[data-baseweb="notification"]:has([data-testid="infoIcon"]) *,
    div[data-testid="stAlert"]:has([data-testid="infoIcon"]) *,
    .stInfo * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="infoIcon"]) svg,
    div[data-testid="stAlert"]:has([data-testid="infoIcon"]) svg,
    .stInfo svg,
    .stInfo [data-testid="infoIcon"] {
        color: #00d4ff !important;
    }
    
    /* Alertas de sucesso - Também azul da marca */
    .stAlert[data-baseweb="notification"]:has([data-testid="successIcon"]),
    div[data-testid="stAlert"]:has([data-testid="successIcon"]),
    .stSuccess {
        background: rgba(0, 212, 255, 0.15) !important;
        border-color: #00d4ff !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="successIcon"]) *,
    div[data-testid="stAlert"]:has([data-testid="successIcon"]) *,
    .stSuccess * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="successIcon"]) svg,
    div[data-testid="stAlert"]:has([data-testid="successIcon"]) svg,
    .stSuccess svg,
    .stSuccess [data-testid="successIcon"] {
        color: #00d4ff !important;
    }
    
    /* Alertas de erro - Vermelho claro */
    .stAlert[data-baseweb="notification"]:has([data-testid="errorIcon"]),
    div[data-testid="stAlert"]:has([data-testid="errorIcon"]),
    .stError {
        background: rgba(255, 107, 107, 0.15) !important;
        border-color: #ff6b6b !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.2) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="errorIcon"]) *,
    div[data-testid="stAlert"]:has([data-testid="errorIcon"]) *,
    .stError * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="errorIcon"]) svg,
    div[data-testid="stAlert"]:has([data-testid="errorIcon"]) svg,
    .stError svg,
    .stError [data-testid="errorIcon"] {
        color: #ff6b6b !important;
    }
    
    /* Alertas de warning - Amarelo */
    .stAlert[data-baseweb="notification"]:has([data-testid="warningIcon"]),
    div[data-testid="stAlert"]:has([data-testid="warningIcon"]),
    .stWarning {
        background: rgba(255, 193, 7, 0.15) !important;
        border-color: #ffc107 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(255, 193, 7, 0.2) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="warningIcon"]) *,
    div[data-testid="stAlert"]:has([data-testid="warningIcon"]) *,
    .stWarning * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="warningIcon"]) svg,
    div[data-testid="stAlert"]:has([data-testid="warningIcon"]) svg,
    .stWarning svg,
    .stWarning [data-testid="warningIcon"] {
        color: #ffc107 !important;
    }
    
    /* Hover effects apenas nos alertas */
    .stAlert[data-baseweb="notification"]:hover,
    div[data-testid="stAlert"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 48px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* Melhorar expanders de planos */
    .streamlit-expanderHeader {
        background: rgba(0, 212, 255, 0.1) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem 1.5rem !important;
        color: #00d4ff !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: #00d4ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(20, 20, 20, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.5rem !important;
        color: #ffffff !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Melhorar alertas padrão do Streamlit */
    .stAlert {
        border-radius: 16px !important;
        border-width: 2px !important;
        padding: 1.25rem !important;
        margin: 1.5rem 0 !important;
        backdrop-filter: blur(10px) !important;
        font-weight: 500 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Alertas de informação */
    .stAlert[data-baseweb="notification"]:has([data-testid="infoIcon"]),
    .stInfo {
        background: rgba(0, 212, 255, 0.25) !important;
        border-color: #00d4ff !important;
        color: #ffffff !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="infoIcon"]) svg,
    .stInfo svg {
        color: #00d4ff !important;
    }
    
    /* Alertas de sucesso - também usar azul padrão */
    .stAlert[data-baseweb="notification"]:has([data-testid="successIcon"]),
    .stSuccess {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: #00d4ff !important;
        color: #ffffff !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="successIcon"]) svg,
    .stSuccess svg {
        color: #00d4ff !important;
    }
    
    /* Alertas de erro */
    .stAlert[data-baseweb="notification"]:has([data-testid="errorIcon"]),
    .stError {
        background: rgba(255, 99, 99, 0.2) !important;
        border-color: #ff6363 !important;
        color: #ffffff !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="errorIcon"]) svg,
    .stError svg {
        color: #ff6363 !important;
    }
    
    /* Alertas de warning */
    .stAlert[data-baseweb="notification"]:has([data-testid="warningIcon"]),
    .stWarning {
        background: rgba(255, 193, 7, 0.2) !important;
        border-color: #ffc107 !important;
        color: #ffffff !important;
    }
    
    .stAlert[data-baseweb="notification"]:has([data-testid="warningIcon"]) svg,
    .stWarning svg {
        color: #ffc107 !important;
    }
    
    /* Melhorar expanders de planos */
    .streamlit-expanderHeader {
        background: rgba(0, 212, 255, 0.1) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem 1.5rem !important;
        color: #00d4ff !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(0, 212, 255, 0.2) !important;
        border-color: #00d4ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(20, 20, 20, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.5rem !important;
        color: #ffffff !important;
        backdrop-filter: blur(10px) !important;
    }
    </style>
    """

def get_chat_theme():
    """Retorna o CSS para a tela do chat - DEPRECADA - Use apply_selected_theme()"""
    # Esta função está deprecada - use apply_selected_theme() para temas dinâmicos
    return ""

# ========================================
# SISTEMA DE CONTROLE DE TEMA
# ========================================

def render_theme_selector():
    """Renderiza o seletor de tema no sidebar"""
    with st.sidebar:
        st.markdown("### 🎨 Tema")
        
        theme_mode = st.radio(
            "Escolha o tema:",
            options=["escuro", "claro"],
            format_func=lambda x: "🌙 Escuro" if x == "escuro" else "☀️ Claro",
            key="theme_mode",
            help="Mude entre tema escuro e claro."
        )
        
        # Indicador visual do tema atual
        if theme_mode == "claro":
            st.markdown("```\n☀️ TEMA CLARO ATIVO\n```")
        else:
            st.markdown("```\n🌙 TEMA ESCURO ATIVO\n```")
        
    return theme_mode

def apply_selected_theme(theme_mode=None):
    """Aplica o tema selecionado"""
    if theme_mode is None:
        theme_mode = st.session_state.get("theme_mode", "escuro")
    
    # Aplica o tema com base na seleção
    if theme_mode == "claro":
        st.markdown(DEEPSEEK_LIGHT_THEME, unsafe_allow_html=True)
        
        # CSS UNIVERSAL PARA GRÁFICOS - Funciona em ambos os temas
        st.markdown("""
        <style>
        /* ESTILO UNIVERSAL PARA GRÁFICOS PLOTLY */
        .stPlotlyChart {
            background: transparent !important;
            border: 1px solid rgba(209, 213, 219, 0.4) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
            margin: 1rem 0 !important;
            overflow: hidden !important;
            transition: all 0.3s ease !important;
        }
        
        .stPlotlyChart:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Container interno transparente */
        .stPlotlyChart .plotly-graph-div,
        .stPlotlyChart .svg-container,
        .stPlotlyChart .plot-container {
            background: transparent !important;
        }
        
        /* Barra de ferramentas elegante */
        .stPlotlyChart .modebar {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(209, 213, 219, 0.6) !important;
            border-radius: 6px !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stPlotlyChart .modebar-btn {
            color: #374151 !important;
        }
        
        .stPlotlyChart .modebar-btn:hover {
            background: rgba(99, 102, 241, 0.1) !important;
            color: #4f46e5 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(DEEPSEEK_DARK_THEME, unsafe_allow_html=True)
        
        # CSS UNIVERSAL PARA GRÁFICOS - Funciona em ambos os temas  
        st.markdown("""
        <style>
        /* ESTILO UNIVERSAL PARA GRÁFICOS PLOTLY */
        .stPlotlyChart {
            background: transparent !important;
            border: 1px solid rgba(209, 213, 219, 0.4) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
            margin: 1rem 0 !important;
            overflow: hidden !important;
            transition: all 0.3s ease !important;
        }
        
        .stPlotlyChart:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Container interno transparente */
        .stPlotlyChart .plotly-graph-div,
        .stPlotlyChart .svg-container,
        .stPlotlyChart .plot-container {
            background: transparent !important;
        }
        
        /* Barra de ferramentas elegante */
        .stPlotlyChart .modebar {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(209, 213, 219, 0.6) !important;
            border-radius: 6px !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stPlotlyChart .modebar-btn {
            color: #374151 !important;
        }
        
        .stPlotlyChart .modebar-btn:hover {
            background: rgba(99, 102, 241, 0.1) !important;
            color: #4f46e5 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    return theme_mode

def create_usage_indicator(current, max_requests, subscription_info=None):
    """Cria o indicador de uso/rate limit integrado com sistema de assinatura"""
    percentage = (current / max_requests) * 100
    color = "#22c55e" if percentage < 70 else "#f59e0b" if percentage < 90 else "#ef4444"
    
    # Se tem informações de assinatura, usa o indicador mais completo
    if subscription_info:
        plan_colors = {
            'free': '#6b7280',      # Cinza
            'basic': '#3b82f6',     # Azul
            'premium': '#8b5cf6',   # Roxo
            'enterprise': '#f59e0b'  # Dourado
        }
        
        plan_icons = {
            'free': '🆓',
            'basic': '📊', 
            'premium': '⭐',
            'enterprise': '👑'
        }
        
        plan_color = plan_colors.get(subscription_info['status'], '#6b7280')
        plan_icon = plan_icons.get(subscription_info['status'], '🆓')
        
        return f"""
        <div class="usage-indicator" style="background: linear-gradient(135deg, {plan_color}15, {plan_color}05); border-left: 3px solid {plan_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: {plan_color}; font-weight: 600; font-size: 12px;">
                    {plan_icon} {subscription_info['description']}
                </span>
                <span style="color: {color}; font-weight: 500;">
                    📊 {current}/{max_requests}
                </span>
            </div>
        </div>
        """
    
    # Fallback para indicador simples
    return f"""
    <div class="usage-indicator">
        <span style="color: {color};">📊 {current}/{max_requests} requisições</span>
    </div>
    """

def show_typing_animation():
    """Mostra animação de typing sutil e integrada"""
    return """
    <div class="typing-indicator">
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <span style="color: var(--text-secondary); font-size: 14px;">Processando...</span>
    </div>
    """

def show_dynamic_processing_animation(step_name: str, step_emoji: str = "⚙️"):
    """
    Mostra animação dinâmica com nome da etapa atual sendo processada
    
    Args:
        step_name: Nome amigável da etapa (ex: "Verificando reutilização", "Executando SQL")
        step_emoji: Emoji representativo da etapa
    """
    return f"""
    <div class="typing-indicator dynamic-processing">
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <span style="color: var(--text-secondary); font-size: 14px;">
            <span style="margin-right: 6px;">{step_emoji}</span>
            {step_name}...
        </span>
    </div>
    """

def get_step_display_info(step_name: str) -> tuple[str, str]:
    """
    Converte nome técnico da etapa para nome amigável e emoji
    
    Returns:
        tuple: (nome_amigável, emoji)
    """
    step_mapping = {
        # Fluxo principal
        'processo_completo': ('Iniciando processamento', '🚀'),
        'verificacao_reuso': ('Verificando reutilização', '🔍'),
        'processamento_reuso': ('Reutilizando dados anteriores', '♻️'),
        'processamento_nova_consulta': ('Preparando nova consulta', '🆕'),
        
        # Fluxo de reuso
        'exibindo_feedback_reuso': ('Preparando dados reutilizados', '📦'),
        'preparando_dados_reuso': ('Organizando dados anteriores', '🔄'),
        'refinamento_gemini_reuso': ('Refinando resposta com IA', '✨'),
        'finalizacao_reuso': ('Finalizando processo', '✅'),
        
        # Fluxo nova consulta
        'preparando_conversa_gemini': ('Preparando contexto', '💬'),
        'envio_gemini_inicial': ('Enviando para IA', '🚀'),
        'validacao_resposta_gemini': ('Validando resposta', '✅'),
        'analise_tipo_resposta': ('Analisando tipo de resposta', '🔍'),
        'preparacao_parametros': ('Preparando parâmetros SQL', '⚙️'),
        'validacao_table_id': ('Validando tabela', '🔒'),
        'construcao_query': ('Construindo consulta SQL', '🔧'),
        'execucao_sql': ('Executando no banco de dados', '💾'),
        'serializacao_dados': ('Processando resultados', '📊'),
        'refinamento_gemini_final': ('Refinando resposta final', '✨'),
        'salvamento_interacao': ('Salvando interação', '💾'),
        'finalizacao_nova_consulta': ('Finalizando consulta', '🏁'),
        'preparando_tech_details': ('Preparando detalhes técnicos', '📋'),
        'preparando_tech_details_final': ('Organizando informações', '📋'),
        'finalizacao_reuso': ('Finalizando reutilização', '🏁')
    }
    
    return step_mapping.get(step_name, (step_name.replace('_', ' ').title(), '⚙️'))

# FUNÇÃO REMOVIDA - Não mais necessária com tema universal

def apply_chart_container_style():
    """
    Aplica estilização de container específica para gráficos Plotly baseada no tema atual.
    Esta função substitui a estilização CSS para evitar conflitos.
    """
    theme_mode = st.session_state.get('theme_mode', 'escuro')
    
    if theme_mode == 'claro':
        container_css = """
        <style>
        /* Container de gráfico - tema claro ELEGANTE */
        .plotly-graph-div {
            border-radius: 12px !important;
            border: 1px solid rgba(209, 213, 219, 0.6) !important;
            background: #ffffff !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
            margin: 1rem 0 !important;
            overflow: hidden !important;
        }
        
        .plotly-graph-div:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.10) !important;
            border-color: rgba(59, 130, 246, 0.4) !important;
        }
        
        /* Garantir que TODOS os elementos do Plotly tenham fundo branco */
        .plotly-graph-div .svg-container,
        .plotly-graph-div .plot-container,
        .plotly-graph-div .main-svg,
        .plotly-graph-div .bg {
            background: #ffffff !important;
            fill: #ffffff !important;
        }
        
        /* Forçar fundo branco em todos os elementos internos */
        .plotly-graph-div * {
            background-color: transparent !important;
        }
        
        /* Estilização específica para container Streamlit Plotly - TEMA CLARO */
        .stPlotlyChart {
            background: #ffffff !important;
            border: 1px solid rgba(209, 213, 219, 0.6) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
            margin: 1rem 0 !important;
            overflow: hidden !important;
            padding: 0.5rem !important;
        }
        
        .stPlotlyChart:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.10) !important;
            border-color: rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-1px) !important;
            transition: all 0.3s ease !important;
        }
        
        /* Garantir que o gráfico interno tenha fundo completamente branco */
        .stPlotlyChart > div,
        .stPlotlyChart .plotly-graph-div,
        .stPlotlyChart .svg-container,
        .stPlotlyChart .plot-container {
            background: #ffffff !important;
            border-radius: 8px !important;
        }
        
        /* Forçar cores escuras nos textos dos gráficos para contraste */
        .stPlotlyChart .plotly-graph-div text {
            fill: #1f2937 !important;
            color: #1f2937 !important;
        }
        
        /* Estilização da barra de ferramentas do Plotly */
        .stPlotlyChart .modebar {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(209, 213, 219, 0.4) !important;
            border-radius: 6px !important;
        }
        
        .stPlotlyChart .modebar-btn {
            color: #374151 !important;
        }
        
        .stPlotlyChart .modebar-btn:hover {
            background: rgba(59, 130, 246, 0.1) !important;
            color: #1d4ed8 !important;
        }
        
        .plotly-graph-div .bg,
        .plotly-graph-div [fill="#000000"],
        .plotly-graph-div [fill="black"] {
            fill: #ffffff !important;
        }
        </style>
        """
    else:  # tema escuro
        container_css = """
        <style>
        /* Container de gráfico - tema escuro */
        .plotly-graph-div {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(15, 15, 23, 0.98) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            margin: 1rem 0 !important;
            overflow: hidden !important;
        }
        
        .plotly-graph-div:hover {
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
            border-color: rgba(0, 212, 255, 0.3) !important;
        }
        </style>
        """
    
    st.markdown(container_css, unsafe_allow_html=True)

def apply_deepseek_theme():
    """Aplica o tema DeepSeek escuro por padrão"""
    st.markdown(DEEPSEEK_DARK_THEME, unsafe_allow_html=True)

def fix_alert_text_visibility():
    """Corrige APENAS a visibilidade do texto em alertas - não mexe no resto do tema"""
    alert_fix_css = """
    <style>
    /* CORREÇÃO ESPECÍFICA PARA TEXTO INVISÍVEL EM ALERTAS */
    [data-testid="stAlert"]:has([data-testid="infoIcon"]) *,
    [data-testid="stAlert"]:has([data-testid="successIcon"]) *,
    [data-testid="stAlert"]:has([data-testid="warningIcon"]) *,
    [data-testid="stAlert"]:has([data-testid="errorIcon"]) * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8) !important;
    }
    </style>
    """
    st.markdown(alert_fix_css, unsafe_allow_html=True)

def get_plans_page_theme():
    """CSS específico para página de planos - preserva layout personalizado"""
    return """
    <style>
    /* APENAS CORES DO TEMA - SEM QUEBRAR LAYOUT DOS CARDS */
    .stApp {
        background: #0a0a0a !important;
        color: #e5e7eb !important;
    }
    
    .block-container {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Preserva os cards customizados da página de planos */
    div[style*="border: 3px solid"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Sidebar tema escuro */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f0f 0%, #1a1a1a 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }
    
    /* Botões do Streamlit com tema azul */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 20, 20, 0.8) !important;
        border-radius: 10px !important;
        padding: 5px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #e5e7eb !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: white !important;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background: rgba(20, 20, 20, 0.6) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Alertas com texto visível */
    [data-testid*="Alert"] * {
        color: white !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
    }
    </style>
    """

def apply_plans_page_theme():
    """Aplica tema específico para página de planos preservando layout"""
    st.markdown("""
    <style>
    /* TEMA ESCURO - APENAS CORES, SEM QUEBRAR LAYOUT */
    .stApp {
        background: #0a0a0a !important;
        color: #e5e7eb !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }
    
    /* SIDEBAR ESCURO */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f0f 0%, #1a1a1a 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }
    
    /* BOTÕES STREAMLIT */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 20, 20, 0.8) !important;
        border-radius: 10px !important;
        padding: 5px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #e5e7eb !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: white !important;
    }
    
    /* REMOVE ELEMENTOS STREAMLIT */
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], 
    .stMainMenu, 
    button[title="View fullscreen"], 
    button[data-testid="baseButton-headerNoPadding"], 
    header[data-testid="stHeader"],
    .stAppDeployButton {
        display: none !important;
    }
    
    /* CRÍTICO: NÃO MEXER NO BLOCK-CONTAINER PARA PRESERVAR CARDS */
    
    /* ALERTAS LEGÍVEIS */
    [data-testid*="Alert"] * {
        color: white !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def fix_alert_visibility():
    """CSS simples para alertas com texto branco legível"""
    st.markdown("""
    <style>
    /* Força texto branco em TODOS os alertas */
    [data-testid*="Alert"],
    [data-testid*="Alert"] *,
    .stAlert,
    .stAlert * {
        color: white !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
    }
    </style>
    """, unsafe_allow_html=True)