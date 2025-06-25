MOBILE_IFRAME_CHAT = """
    <style>
        @media screen and (max-width: 768px) {
            /* Mensagens de chat mais compactas */
            .stChatMessage {
                padding: 0.75rem !important;
                margin-bottom: 0.5rem !important;
                border-radius: 12px !important;
            }
            
            /* Texto mais legível em mobile */
            .stMarkdown p, .stMarkdown li {
                font-size: 0.9rem !important;
                line-height: 1.4 !important;
            }
            
            /* Tabelas mais compactas */
            .stMarkdown table {
                font-size: 0.8rem !important;
            }
            
            /* Expanders mais compactos */
            .stExpander summary {
                padding: 0.5rem !important;
            }
            
            /* Código mais legível */
            .stCodeBlock {
                font-size: 0.8rem !important;
                padding: 0.5rem !important;
            }
        }
        
        /* Melhor contraste para o spoiler técnico */
        .streamlit-expanderHeader {
            background-color: #f0f2f6;
        }
        
        /* Espaçamento melhorado entre mensagens */
        .stChatMessage:not(:last-child) {
            margin-bottom: 0.75rem !important;
        }
    </style>
"""

MOBILE_IFRAME_BASE = """
    <style>
        /*limpando menu de navegação*/
        .reportview-container {
            margin-top: -2em;
        }
        .stAppDeployButton {display:none;}
        #stDecoration {display:none;}
        
        /* Remove espaço acima do título */
        .stApp {
            margin-top: -7px;
        }
        /* Ajusta o header do Streamlit */
        header[data-testid="stHeader"] {
            background: none;
            height: 0px;
        }
        /* Remove o padding extra */
        .block-container {
            padding-top: 1rem;
            padding-bottom: -10rem;
        }
        
        /* Esconde o botão Deploy */
        [data-testid="stDeployButton"] {
            display: none;
        }
        /* Esconde o menu hamburguer se necessário */
        [data-testid="collapsedControl"] {
            display: none;
        }
        
        /* Container fixo APENAS para mobile */
        @media screen and (max-width: 768px) {
            .mobile-input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: #000000;
                padding: 0.8rem;
                z-index: 100;
                border-top: 1px solid #333;
            }
            
            h1 {
                font-size: 1.5rem !important;
                margin-bottom: 0.5rem !important;
                padding-top: 0.5rem !important;
            }
            
            .stChatMessage {
                padding: 0.75rem !important;
            }
            
            .stExpander {
                margin-top: 0.5rem !important;
            }
            
            .stCodeBlock {
                font-size: 0.8rem !important;
            }
        }
        
        /* Estilo do input em ambos os casos */
        .stChatInput textarea {
            color: white !important;
        }
        
        .stChatInput textarea::placeholder {
            color: #ccc !important;
        }
        
        .stChatInput {
            bottom: -40px !important;  /* Aumenta a distância do rodapé */
            padding: 10px !important;
            background: transparent !important;
        }
        
    </style>
"""

