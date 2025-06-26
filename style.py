MOBILE_IFRAME_CHAT = """
    <style>
        @media screen and (max-width: 768px) {
            .stChatMessage {
                padding: 0.75rem !important;
                margin-bottom: 0.5rem !important;
                border-radius: 12px !important;
            }
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
            }
        }
        .streamlit-expanderHeader {
            background-color: #f0f2f6;
        }
        .stChatMessage:not(:last-child) {
            margin-bottom: 0.75rem !important;
        }

        /* DARK MODE */
        body.dark .stChatInput textarea {
            background: #222 !important;
            color: #fff !important;
            border-radius: 8px !important;
        }
        body.dark .stChatInput textarea::placeholder {
            color: #ccc !important;
        }
        body.dark .stChatInput {
            background: #181c24 !important;
        }

        /* LIGHT MODE */
        body.light .stChatInput textarea {
            background: #e3eafc !important;
            color: #1a237e !important;
            border-radius: 8px !important;
        }
        body.light .stChatInput textarea::placeholder {
            color: #5c6bc0 !important;
        }
        body.light .stChatInput {
            background: #f8fafd !important;
        }
    </style>
"""

MOBILE_IFRAME_BASE = """
    <style>
        .reportview-container { margin-top: -2em; }
        .stAppDeployButton {display:none;}
        #stDecoration {display:none;}
        .stApp { margin-top: -7px; }
        header[data-testid="stHeader"] { background: none; height: 0px; }
        .block-container { padding-top: 1rem; padding-bottom: -10rem; }
        [data-testid="stDeployButton"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
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
            .stChatMessage { padding: 0.75rem !important; }
            .stExpander { margin-top: 0.5rem !important; }
            .stCodeBlock { font-size: 0.8rem !important; }
        }
        /* DARK MODE */
        body.dark .stChatInput textarea {
            background: #222 !important;
            color: #fff !important;
            border-radius: 8px !important;
        }
        body.dark .stChatInput textarea::placeholder {
            color: #ccc !important;
        }
        body.dark .stChatInput {
            background: #181c24 !important;
        }
        /* LIGHT MODE */
        body.light .stChatInput textarea {
            background: #e3eafc !important;
            color: #1a237e !important;
            border-radius: 8px !important;
        }
        body.light .stChatInput textarea::placeholder {
            color: #5c6bc0 !important;
        }
        body.light .stChatInput {
            background: #f8fafd !important;
        }
    </style>
"""