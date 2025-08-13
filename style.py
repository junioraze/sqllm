MOBILE_IFRAME_CHAT = """
    <style>
        /* FUNDO E ESTRUTURA MOBILE */
        .stApp > div:first-child {
            background: url('etc/fundo.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }
        
        .block-container, [data-testid="stBottomBlockContainer"] {
            background: rgba(255, 140, 66, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 15px !important;
            margin: 1rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px rgba(255, 107, 53, 0.3) !important;
            border: 1px solid rgba(255, 140, 66, 0.4) !important;
        }
        
        /* OCULTA ELEMENTOS DESNECESSÁRIOS */
        [data-testid="stToolbar"], .stToolbar, [data-testid="stDecoration"], 
        [data-testid="stStatusWidget"], .stMainMenu, button[title="View fullscreen"], 
        button[data-testid="baseButton-headerNoPadding"], [data-testid="stSidebar"],
        header[data-testid="stHeader"] { display: none !important; }
        
        /* CHAT - APENAS LAYOUT, SEM CORES */
        .stChatMessage {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(5px) !important;
            border-radius: 12px !important;
            margin-bottom: 0.75rem !important;
            padding: 0.75rem !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }
        
        /* EXPANDIR MOBILE - APENAS LAYOUT */
        .stExpander {
            background: rgba(255, 255, 255, 0.95) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }
        
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.9) !important;
            font-weight: 600 !important;
        }
        
        /* INTERFACE MOBILE OTIMIZADA */
        .stApp { padding-top: 1rem !important; }
        .main .block-container { padding-top: 1rem !important; }
        h1 { font-size: 1.8rem !important; margin-bottom: 1rem !important; }
        .stChatInput { margin-top: 1rem !important; }
    </style>
"""

MOBILE_IFRAME_BASE = """
    <style>
        /* ELEMENTOS BÁSICOS MOBILE */
        .reportview-container { margin-top: -2em; }
        .stApp { margin-top: -7px; }
        .block-container { padding-top: 1rem; padding-bottom: -10rem; }
        
        /* OCULTA ELEMENTOS DESNECESSÁRIOS */
        .stAppDeployButton, #stDecoration, [data-testid="stDeployButton"], 
        [data-testid="collapsedControl"], [data-testid="stToolbar"], .stToolbar, 
        [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stMainMenu, 
        button[title="View fullscreen"], button[data-testid="baseButton-headerNoPadding"], 
        [data-testid="stSidebar"], header[data-testid="stHeader"] { display: none !important; }
        
        /* CHAT INPUT LARANJA */
        .stChatInput textarea {
            background: rgba(255, 107, 53, 0.9) !important;
            color: #fff !important;
            border-radius: 8px !important;
            backdrop-filter: blur(5px) !important;
            border: 1px solid rgba(255, 140, 66, 0.6) !important;
        }
        
        .stChatInput textarea::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        
        .stChatInput {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* RESPONSIVO - SEM CORES */
        @media screen and (max-width: 768px) {
            h1 {
                font-size: 1.5rem !important;
                margin-bottom: 0.5rem !important;
                padding-top: 0.5rem !important;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
            }
        }
    </style>
"""
