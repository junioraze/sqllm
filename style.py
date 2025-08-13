MOBILE_IFRAME_CHAT = """
    <style>
        /* CHATBOT BACKGROUND COM IMAGEM */
        .stApp > div:first-child {
            background: url('etc/fundo.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }
        
        /* CONTAINER PRINCIPAL COM TRANSPARÊNCIA LARANJA MAIS SUAVE */
        .block-container {
            background: rgba(255, 140, 66, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 15px !important;
            margin: 1rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px rgba(255, 107, 53, 0.3) !important;
            border: 1px solid rgba(255, 140, 66, 0.4) !important;
        }
        
        /* BOTTOM BLOCK CONTAINER COM MESMO PADRÃO */
        [data-testid="stBottomBlockContainer"] {
            background: rgba(255, 140, 66, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 15px !important;
            border: 1px solid rgba(255, 140, 66, 0.4) !important;
            box-shadow: 0 4px 6px rgba(255, 107, 53, 0.3) !important;
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
        
        /* MENSAGENS DE CHAT COM TEMA LARANJA MAIS SUAVE */
        .stChatMessage {
            background: rgba(255, 140, 66, 0.5) !important;
            backdrop-filter: blur(5px) !important;
            border-radius: 12px !important;
            margin-bottom: 0.75rem !important;
            padding: 0.75rem !important;
            border: 1px solid rgba(255, 107, 53, 0.5) !important;
            color: #fff !important;
        }
        
        /* GRÁFICOS PLOTLY COM FUNDO LARANJA MAIS SUAVE */
        .js-plotly-plot .plotly {
            background: rgba(255, 140, 66, 0.4) !important;
            border-radius: 12px !important;
        }
        
        .js-plotly-plot .plotly .bg {
            fill: rgba(255, 140, 66, 0.4) !important;
        }
        
        .js-plotly-plot .plotly .plot-container {
            background: rgba(255, 140, 66, 0.4) !important;
            border-radius: 12px !important;
        }
        
        .stPlotlyChart > div {
            background: rgba(255, 140, 66, 0.4) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(5px) !important;
        }
        
        /* MELHORIAS DE FONTE PARA GRÁFICOS MOBILE */
        .js-plotly-plot text {
            font-family: 'Arial', sans-serif !important;
            font-weight: 600 !important;
            fill: white !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important;
        }
        
        .js-plotly-plot .xtick text, .js-plotly-plot .ytick text {
            font-size: 12px !important;
            font-weight: 600 !important;
            fill: white !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7) !important;
        }
        
        .js-plotly-plot .g-xtitle text, .js-plotly-plot .g-ytitle text {
            font-size: 13px !important;
            font-weight: 700 !important;
            fill: white !important;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
        }
        
        .js-plotly-plot .gtitle text {
            font-size: 16px !important;
            font-weight: 700 !important;
            fill: white !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8) !important;
        }
        
        .js-plotly-plot .legend text {
            font-size: 11px !important;
            font-weight: 600 !important;
            fill: white !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7) !important;
        }
        
        /* EXPANSORES COM TEMA LARANJA MAIS SUAVE */
        .stExpander {
            background: rgba(255, 140, 66, 0.5) !important;
            backdrop-filter: blur(5px) !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 107, 53, 0.5) !important;
        }
        
        .streamlit-expanderHeader {
            background: rgba(255, 107, 53, 0.6) !important;
            backdrop-filter: blur(5px) !important;
            color: #fff !important;
        }

        /* CHAT INPUT COM TEMA LARANJA */
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
                background: rgba(255, 140, 66, 0.9) !important;
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
        
        /* CHAT INPUT COM TEMA LARANJA */
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
        
        /* RESPONSIVO MOBILE */
        @media screen and (max-width: 768px) {
            .mobile-input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: rgba(255, 107, 53, 0.7);
                padding: 0.8rem;
                z-index: 100;
                border-top: 1px solid rgba(255, 140, 66, 0.6);
                backdrop-filter: blur(10px);
            }
            h1 {
                font-size: 1.5rem !important;
                margin-bottom: 0.5rem !important;
                padding-top: 0.5rem !important;
                color: #fff !important;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
            }
            .stCodeBlock { 
                font-size: 0.8rem !important; 
                background: rgba(255, 140, 66, 0.9) !important;
                backdrop-filter: blur(5px) !important;
            }
        }
    </style>
"""