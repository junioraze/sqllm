# DeepSeek Theme System - Arquitetura Unificada e Limpa
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
    
    --gradient-title: linear-gradient(135deg, #00d4ff 0%, #00a8cc 50%, #0066ff 100%);
    --gradient-button: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
    --gradient-download: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    --gradient-user: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 168, 204, 0.15) 100%);
    --gradient-assistant: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
    --gradient-shimmer: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    --gradient-scrollbar: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
    --gradient-scrollbar-hover: linear-gradient(135deg, #00a8cc 0%, #0052cc 100%);
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
    --shadow-focus: 0 0 20px rgba(14, 165, 233, 0.3);
    --shadow-button: 0 4px 15px rgba(14, 165, 233, 0.3);
    --shadow-button-hover: 0 6px 25px rgba(14, 165, 233, 0.5);
    
    --gradient-title: linear-gradient(135deg, #0066ff 0%, #00a8cc 50%, #00d4ff 100%);
    --gradient-button: linear-gradient(135deg, #0ea5e9 0%, #0066ff 100%);
    --gradient-download: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    --gradient-user: linear-gradient(135deg, rgba(0, 102, 255, 0.1) 0%, rgba(0, 168, 204, 0.1) 100%);
    --gradient-assistant: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
    --gradient-shimmer: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.1), transparent);
    --gradient-scrollbar: linear-gradient(135deg, #0ea5e9 0%, #0066ff 100%);
    --gradient-scrollbar-hover: linear-gradient(135deg, #0284c7 0%, #0052cc 100%);
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
    """Retorna o CSS para a tela de login com inputs padronizados"""
    return """
    <style>
    /* BASE LOGIN THEME */
    .stApp, .main, [data-testid="stAppViewContainer"], .block-container {
        background: #0a0a0a !important;
        color: #e5e7eb !important;
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
    .stAppDeployButton,
    #stDecoration {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    /* INPUTS DE LOGIN */
    .stTextInput input, .stPasswordInput input {
        background: rgba(25, 25, 25, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input::placeholder, .stPasswordInput input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
        font-style: italic !important;
    }
    
    .stTextInput label, .stPasswordInput label {
        color: #e5e7eb !important;
        font-weight: 500 !important;
    }
    
    .stTextInput input:focus, .stPasswordInput input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
        outline: none !important;
    }
    
    /* BOTÕES DE LOGIN */
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

def create_usage_indicator(current, max_requests):
    """Cria o indicador de uso/rate limit"""
    percentage = (current / max_requests) * 100
    color = "#22c55e" if percentage < 70 else "#f59e0b" if percentage < 90 else "#ef4444"
    
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