import base64
import os
from pathlib import Path

def get_base64_image(image_path):
    """Converte uma imagem para base64 para uso em CSS"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Erro ao carregar imagem {image_path}: {e}")
        return None

def get_background_style():
    """Retorna o estilo CSS com a imagem de fundo em base64"""
    background_path = os.path.join(os.path.dirname(__file__), "etc", "fundo.jpg")
    base64_bg = get_base64_image(background_path)
    
    if base64_bg:
        return f"""
        <style>
            /* FUNDO GLOBAL COM IMAGEM */
            .stApp, .stApp > div:first-child, [data-testid="stAppViewContainer"], 
            [data-testid="stHeader"], .main, .stMainBlockContainer {{
                background: url('data:image/jpeg;base64,{base64_bg}') !important;
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
                background-repeat: no-repeat !important;
            }}
            
            /* FORÇA O FUNDO EM TODA A HIERARQUIA */
            body, html, #root, [data-testid="stApp"] {{
                background: url('data:image/jpeg;base64,{base64_bg}') !important;
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
                background-repeat: no-repeat !important;
            }}
            
            /* REMOVE FUNDOS PADRÃO DO STREAMLIT */
            .stApp > header, .stApp > div, .stApp section {{
                background: transparent !important;
            }}
            
            /* CONTAINERS COM TRANSPARÊNCIA LARANJA MAIS SUAVE */
            .block-container {{
                background: rgba(255, 140, 66, 0.3) !important;
                backdrop-filter: blur(15px) !important;
                border-radius: 20px !important;
                margin: 1rem !important;
                padding: 2rem !important;
                box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3) !important;
                border: 1px solid rgba(255, 140, 66, 0.4) !important;
            }}
            
            /* BOTTOM BLOCK CONTAINER COM MESMO PADRÃO */
            [data-testid="stBottomBlockContainer"] {{
                background: rgba(255, 140, 66, 0.3) !important;
                backdrop-filter: blur(15px) !important;
                border-radius: 20px !important;
                border: 1px solid rgba(255, 140, 66, 0.4) !important;
                box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3) !important;
            }}
            
            /* MENSAGENS DE CHAT - APENAS LAYOUT */
            .stChatMessage {{
                background: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 15px !important;
                margin-bottom: 1rem !important;
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
            }}
            
            /* EXPANSOR - APENAS LAYOUT */
            .stExpander {{
                background: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 12px !important;
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
            }}
            
            .streamlit-expanderHeader {{
                background: rgba(255, 255, 255, 0.9) !important;
                backdrop-filter: blur(8px) !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }}
            
            /* GRÁFICOS PLOTLY COM FUNDO BRANCO */
            .js-plotly-plot .plotly {{
                background: rgba(255, 255, 255, 0.95) !important;
                border-radius: 12px !important;
            }}
            
            .js-plotly-plot .plotly .bg {{
                fill: rgba(255, 255, 255, 0.95) !important;
            }}
            
            .js-plotly-plot .plotly .plot-container {{
                background: rgba(255, 255, 255, 0.95) !important;
                border-radius: 12px !important;
            }}
            
            .stPlotlyChart > div {{
                background: rgba(255, 255, 255, 0.95) !important;
                border-radius: 12px !important;
                backdrop-filter: blur(10px) !important;
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                min-height: 500px !important;  /* Altura mínima para evitar compressão */
                height: auto !important;       /* Permite ajuste automático */
            }}
            
            /* CONTAINER DOS GRÁFICOS - ALTURA FIXA */
            .stPlotlyChart {{
                min-height: 500px !important;
                height: 600px !important;
            }}
            
            /* PLOT CONTAINER - DIMENSÕES ADEQUADAS */
            .js-plotly-plot .plotly .plot-container .plotly .main-svg {{
                min-height: 450px !important;
            }}
            
            /* MELHORIAS DE FONTE PARA GRÁFICOS - APENAS LAYOUT */
            .js-plotly-plot text {{
                font-family: 'Arial', sans-serif !important;
                font-weight: 600 !important;
                text-shadow: none !important;
            }}
            
            .js-plotly-plot .xtick text, .js-plotly-plot .ytick text {{
                font-size: 13px !important;
                font-weight: 600 !important;
                text-shadow: none !important;
            }}
            
            .js-plotly-plot .g-xtitle text, .js-plotly-plot .g-ytitle text {{
                font-size: 14px !important;
                font-weight: 700 !important;
                text-shadow: none !important;
            }}
            
            .js-plotly-plot .gtitle text {{
                font-size: 18px !important;
                font-weight: 700 !important;
                text-shadow: none !important;
            }}
            
            .js-plotly-plot .legend text {{
                font-size: 12px !important;
                font-weight: 600 !important;
                text-shadow: none !important;
            }}
            
            /* HOVER LABELS - APENAS LAYOUT */
            .js-plotly-plot .hovertext {{
                background: rgba(255, 255, 255, 0.95) !important;
                border: 1px solid rgba(0, 0, 0, 0.2) !important;
                font-size: 12px !important;
                font-weight: 600 !important;
            }}
            
            /* INPUT DE CHAT COM TEMA LARANJA MAIS SUAVE */
            .stChatInput textarea {{
                background: rgba(255, 107, 53, 0.7) !important;
                border-radius: 12px !important;
                border: 2px solid rgba(255, 140, 66, 0.6) !important;
                padding: 0.8rem !important;
                font-size: 1rem !important;
                transition: all 0.3s ease !important;
            }}
            
            .stChatInput textarea:focus {{
                border-color: rgba(255, 140, 66, 0.8) !important;
                box-shadow: 0 0 0 3px rgba(255, 140, 66, 0.3) !important;
            }}
            
            .stChatInput textarea::placeholder {{
                color: rgba(255, 255, 255, 0.8) !important;
            }}
            
            /* CONTAINER DO INPUT TRANSPARENTE */
            .stChatInput {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            
            .stChatInput > div {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                backdrop-filter: none !important;
            }}
            
            /* RESPONSIVO MOBILE */
            @media screen and (max-width: 768px) {{
                .block-container {{
                    margin: 0.5rem !important;
                    padding: 1rem !important;
                    border-radius: 15px !important;
                }}
                
                .stChatMessage {{
                    padding: 0.75rem !important;
                    margin-bottom: 0.5rem !important;
                    border-radius: 12px !important;
                }}
                
                .stMarkdown p, .stMarkdown li {{
                    font-size: 0.9rem !important;
                    line-height: 1.4 !important;
                }}
                
                /* PRESERVA CORES DOS SPANS IA EM MARKDOWN */
                .stMarkdown .ia-highlight,
                .stMarkdown span[style*="color: #ff6b35"],
                .stMarkdown span[style*="color:#ff6b35"] {{
                    color: #ff6b35 !important;
                }}
                
                .stMarkdown table {{
                    font-size: 0.8rem !important;
                }}
                
                .stExpander summary {{
                    padding: 0.5rem !important;
                }}
                
                .stCodeBlock {{
                    font-size: 0.8rem !important;
                    padding: 0.5rem !important;
                    background: rgba(255, 140, 66, 0.9) !important;
                    backdrop-filter: blur(5px) !important;
                }}
            }}
        </style>
        """
    else:
        # Fallback com gradiente laranja
        return """
        <style>
            .stApp > div:first-child {
                background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
            }
            .block-container {
                background: rgba(255, 140, 66, 0.3) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 15px !important;
                margin: 1rem !important;
                padding: 1.5rem !important;
                box-shadow: 0 4px 6px rgba(255, 107, 53, 0.3) !important;
            }
            
            .stChatInput {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            
            .stChatInput > div {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            
            .stChatInput textarea {
                background: rgba(255, 107, 53, 0.7) !important;
                border-radius: 8px !important;
                border: 1px solid rgba(255, 140, 66, 0.6) !important;
            }
        </style>
        """

def get_login_background_style():
    """Retorna o estilo CSS simplificado para a tela de login"""
    return """
    <style>
        /* LOGIN BACKGROUND COM IMAGEM */
        .stApp > div:first-child {
            background: url('etc/fundo.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }
        
        /* REMOVE ELEMENTOS DESNECESSÁRIOS NO LOGIN */
        [data-testid="stToolbar"], .stToolbar, [data-testid="stDecoration"], 
        [data-testid="stStatusWidget"], .stMainMenu, button[title="View fullscreen"], 
        button[data-testid="baseButton-headerNoPadding"], [data-testid="stSidebar"],
        header[data-testid="stHeader"] { display: none !important; }
        
        /* CONTAINER DE LOGIN */
        .block-container {
            background: rgba(255, 140, 66, 0.3) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 15px !important;
            max-width: 500px !important;
            margin: 2rem auto !important;
            padding: 2rem !important;
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4) !important;
            border: 1px solid rgba(255, 140, 66, 0.6) !important;
        }
        
        /* CAMPOS DE INPUT LARANJA - APENAS LAYOUT */
        .stTextInput > div > div > input {
            background: rgba(255, 107, 53, 0.9) !important;
            border: 1px solid rgba(255, 140, 66, 0.6) !important;
            border-radius: 6px !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        
        /* LABELS - APENAS LAYOUT */
        .stTextInput > label {
            font-weight: 500 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* BOTÃO ENTRAR - APENAS LAYOUT */
        .stButton > button {
            width: 100% !important;
            background: rgba(255, 107, 53, 0.95) !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
    </style>
    """


