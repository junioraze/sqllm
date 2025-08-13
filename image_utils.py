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
            
            /* CONTAINERS COM TRANSPARÊNCIA LARANJA MAIS INTENSA */
            .block-container {{
                background: rgba(255, 140, 66, 0.45) !important;
                backdrop-filter: blur(15px) !important;
                border-radius: 20px !important;
                margin: 1rem !important;
                padding: 2rem !important;
                box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3) !important;
                border: 1px solid rgba(255, 140, 66, 0.4) !important;
            }}
            
            /* MENSAGENS DE CHAT ELEGANTES */
            .stChatMessage {{
                background: rgba(255, 140, 66, 0.7) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 15px !important;
                margin-bottom: 1rem !important;
                border: 1px solid rgba(255, 107, 53, 0.5) !important;
                box-shadow: 0 4px 16px rgba(255, 107, 53, 0.2) !important;
                color: #fff !important;
            }}
            
            /* EXPANSORES ELEGANTES */
            .stExpander {{
                background: rgba(255, 140, 66, 0.8) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 12px !important;
                border: 1px solid rgba(255, 107, 53, 0.5) !important;
                box-shadow: 0 4px 16px rgba(255, 107, 53, 0.15) !important;
            }}
            
            .streamlit-expanderHeader {{
                background: rgba(255, 107, 53, 0.9) !important;
                backdrop-filter: blur(8px) !important;
                border-radius: 8px !important;
                color: #fff !important;
            }}
            
            /* INPUT DE CHAT COM TEMA LARANJA */
            .stChatInput textarea {{
                background: rgba(255, 107, 53, 0.9) !important;
                color: #fff !important;
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
                background: rgba(255, 140, 66, 0.45) !important;
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
                background: rgba(255, 107, 53, 0.9) !important;
                color: #fff !important;
                border-radius: 8px !important;
                border: 1px solid rgba(255, 140, 66, 0.6) !important;
            }
        </style>
        """

def get_login_background_style():
    """Retorna o estilo CSS para a tela de login"""
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
        
        /* REMOVE MENU HAMBÚRGUER NO LOGIN */
        [data-testid="stToolbar"] { display: none !important; }
        .stToolbar { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stStatusWidget"] { display: none !important; }
        .stMainMenu { display: none !important; }
        button[title="View fullscreen"] { display: none !important; }
        button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        
        /* CONTAINER DE LOGIN COM TRANSPARÊNCIA LARANJA MAIS INTENSA */
        .block-container {
            background: rgba(255, 140, 66, 0.45) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 15px !important;
            max-width: 500px !important;
            width: 85% !important;
            margin: 0.2rem auto !important;
            padding: 0.7rem 1.2rem !important;
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4) !important;
            border: 1px solid rgba(255, 140, 66, 0.6) !important;
            min-height: auto !important;
            position: relative !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
        }
        
        h1 {
            text-align: center !important;
            color: #fff !important;
            margin-bottom: 0.3rem !important;
            margin-top: 0 !important;
            font-weight: 600 !important;
            font-size: 1.4rem !important;
            line-height: 1.2 !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* CAMPOS DE INPUT */
        .stTextInput {
            margin-bottom: 0.3rem !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(255, 107, 53, 0.9) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 140, 66, 0.6) !important;
            border-radius: 6px !important;
            padding: 0.4rem 0.7rem !important;
            font-size: 0.9rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            height: 38px !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        
        .stTextInput > div > div > input:focus {
            box-shadow: 0 0 0 2px rgba(255, 140, 66, 0.5) !important;
            border-color: rgba(255, 140, 66, 0.8) !important;
        }
        
        /* LABELS DOS INPUTS */
        .stTextInput > label {
            color: #fff !important;
            font-weight: 500 !important;
            margin-bottom: 0.2rem !important;
            font-size: 0.85rem !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* BOTÃO ENTRAR */
        .stButton > button {
            width: 100% !important;
            background: rgba(255, 107, 53, 0.95) !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.4rem 1rem !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            margin-top: 0.3rem !important;
            transition: all 0.3s ease !important;
            height: 38px !important;
            box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4) !important;
            background: rgba(255, 107, 53, 1) !important;
        }
        
        .stAlert {
            border-radius: 8px !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0 !important;
            background: rgba(255, 140, 66, 0.9) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 107, 53, 0.6) !important;
        }
        
        @media screen and (max-width: 768px) {
            .block-container {
                margin: 0.1rem !important;
                max-width: none !important;
                width: 92% !important;
                padding: 0.6rem 0.8rem !important;
                transform: none !important;
                top: auto !important;
                position: static !important;
            }
            
            h1 {
                font-size: 1.2rem !important;
                margin-bottom: 0.2rem !important;
            }
            
            .stTextInput {
                margin-bottom: 0.25rem !important;
            }
            
            .stTextInput > label {
                font-size: 0.8rem !important;
                margin-bottom: 0.15rem !important;
            }
            
            .stTextInput > div > div > input {
                padding: 0.35rem 0.5rem !important;
                font-size: 0.85rem !important;
                height: 35px !important;
            }
            
            .stButton > button {
                padding: 0.35rem 0.7rem !important;
                font-size: 0.85rem !important;
                margin-top: 0.25rem !important;
                height: 35px !important;
            }
        }
    </style>
    """

def create_header_with_images():
    """Cria um header elegante com nome e logo da empresa"""
    try:
        # Caminho para as imagens
        nome_path = os.path.join(os.path.dirname(__file__), "etc", "nome_logo.jpg")
        logo_path = os.path.join(os.path.dirname(__file__), "etc", "logo_quadrada.jpg")
        
        # Estilo CSS para o header
        header_style = """
        <style>
            .custom-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 1rem 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .header-logo {
                height: 60px;
                width: 60px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .header-name {
                flex: 1;
                margin: 0 1rem;
                height: 40px;
                object-fit: contain;
            }
            
            [data-theme="dark"] .custom-header {
                background: rgba(25, 25, 25, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            @media screen and (max-width: 768px) {
                .custom-header {
                    padding: 0.75rem 1rem;
                    margin-bottom: 1rem;
                }
                
                .header-logo {
                    height: 45px;
                    width: 45px;
                }
                
                .header-name {
                    height: 30px;
                }
            }
        </style>
        """
        
        # HTML do header
        header_html = f"""
        {header_style}
        <div class="custom-header">
            <img src="data:image/jpeg;base64,{get_base64_image(logo_path)}" class="header-logo" alt="Logo">
            <img src="data:image/jpeg;base64,{get_base64_image(nome_path)}" class="header-name" alt="Nome da Empresa">
            <img src="data:image/jpeg;base64,{get_base64_image(logo_path)}" class="header-logo" alt="Logo">
        </div>
        """
        
        return header_html if get_base64_image(nome_path) and get_base64_image(logo_path) else ""
        
    except Exception as e:
        print(f"Erro ao criar header: {e}")
        return ""
