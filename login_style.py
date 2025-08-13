LOGIN_SCREEN_STYLE = """
    <style>
        /* LOGIN BACKGROUND */
        .stApp > div:first-child {
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('etc/fundo.jpg') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
            min-height: 100vh !important;
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
        
        .block-container {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 20px !important;
            max-width: 600px !important;
            width: 90% !important;
            margin: 0.5rem auto !important;
            padding: 1rem 1.5rem !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            min-height: auto !important;
        }
        
        .login-logo {
            display: block;
            margin: 0 auto 2rem auto;
            max-width: 200px;
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        h1 {
            text-align: center !important;
            color: #333 !important;
            margin-bottom: 0.5rem !important;
            font-weight: 600 !important;
            font-size: 1.6rem !important;
        }
        
        .stTextInput {
            margin-bottom: 0.5rem !important;
        }
        
        .stTextInput > div > div > input {
            background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 0.5rem 0.8rem !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        
        .stTextInput > div > div > input:focus {
            box-shadow: 0 0 0 2px rgba(255, 140, 66, 0.3) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
        }
        
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.2rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            margin-top: 0.5rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(255, 140, 66, 0.3) !important;
        }
        
        .stAlert {
            border-radius: 8px !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0 !important;
        }
        
        @media screen and (max-width: 768px) {
            .block-container {
                margin: 0.3rem !important;
                max-width: none !important;
                width: 95% !important;
                padding: 0.8rem !important;
            }
            
            .login-logo {
                max-width: 120px;
                margin-bottom: 1rem;
            }
            
            h1 {
                font-size: 1.3rem !important;
                margin-bottom: 0.4rem !important;
            }
            
            .stTextInput {
                margin-bottom: 0.4rem !important;
            }
            
            .stTextInput > div > div > input {
                padding: 0.4rem 0.6rem !important;
                font-size: 0.9rem !important;
            }
            
            .stButton > button {
                padding: 0.4rem 0.8rem !important;
                font-size: 0.9rem !important;
                margin-top: 0.4rem !important;
            }
        }
    </style>
"""
