MOBILE_IFRAME_CHAT = """
    <style>
        /* CHATBOT BACKGROUND */
        .stApp > div:first-child {
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('etc/fundo.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }
        
        .block-container {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 15px !important;
            margin: 1rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* REMOVE MENU HAMBÚRGUER */
        [data-testid="stToolbar"] { display: none !important; }
        .stToolbar { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stStatusWidget"] { display: none !important; }
        .stMainMenu { display: none !important; }
        button[title="View fullscreen"] { display: none !important; }
        button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        
        /* MENSAGENS DE CHAT */
        .stChatMessage {
            background: rgba(255, 255, 255, 0.9) !important;
            backdrop-filter: blur(5px) !important;
            border-radius: 12px !important;
            margin-bottom: 0.75rem !important;
            padding: 0.75rem !important;
        }
        
        /* EXPANSORES */
        .stExpander {
            background: rgba(255, 255, 255, 0.9) !important;
            backdrop-filter: blur(5px) !important;
            border-radius: 8px !important;
        }
        
        .streamlit-expanderHeader {
            background-color: rgba(240, 242, 246, 0.9) !important;
            backdrop-filter: blur(5px) !important;
        }

        /* CHAT INPUT STYLING */
        .stChatInput textarea {
            background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
            color: #fff !important;
            border-radius: 8px !important;
            backdrop-filter: blur(5px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .stChatInput textarea::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        .stChatInput {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* RESPONSIVO MOBILE */
        @media screen and (max-width: 768px) {
            .stMarkdown p, .stMarkdown li {
                font-size: 0.9rem !important;
                line-height: 1.4 !important;
            }
            .stMarkdown table {
                font-size: 0.8rem !important;
            }
            .stExpander summary {
                padding: 0.5rem !important;
            }
            .stCodeBlock {
                font-size: 0.8rem !important;
                padding: 0.5rem !important;
                background: rgba(248, 250, 253, 0.9) !important;
                backdrop-filter: blur(5px) !important;
            }
        }
    </style>
"""

MOBILE_IFRAME_BASE = """
    <style>
        /* REMOVE ELEMENTOS DESNECESSÁRIOS DO STREAMLIT */
        .reportview-container { margin-top: -2em; }
        .stAppDeployButton {display:none;}
        #stDecoration {display:none;}
        .stApp { margin-top: -7px; }
        header[data-testid="stHeader"] { background: none; height: 0px; }
        .block-container { padding-top: 1rem; padding-bottom: -10rem; }
        [data-testid="stDeployButton"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        
        /* REMOVE MENU HAMBÚRGUER */
        [data-testid="stToolbar"] { display: none !important; }
        .stToolbar { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stStatusWidget"] { display: none !important; }
        .stMainMenu { display: none !important; }
        button[title="View fullscreen"] { display: none !important; }
        button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        
        /* CHAT INPUT STYLING COMPLEMENTAR */
        .stChatInput textarea {
            background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
            color: #fff !important;
            border-radius: 8px !important;
            backdrop-filter: blur(5px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .stChatInput textarea::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        .stChatInput {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* RESPONSIVO MOBILE */
        @media screen and (max-width: 768px) {
            .mobile-input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: rgba(0, 0, 0, 0.9);
                padding: 0.8rem;
                z-index: 100;
                border-top: 1px solid #333;
                backdrop-filter: blur(10px);
            }
            h1 {
                font-size: 1.5rem !important;
                margin-bottom: 0.5rem !important;
                padding-top: 0.5rem !important;
            }
            .stCodeBlock { 
                font-size: 0.8rem !important; 
                background: rgba(248, 250, 253, 0.9) !important;
                backdrop-filter: blur(5px) !important;
            }
        }
    </style>
"""