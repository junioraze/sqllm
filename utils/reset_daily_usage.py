import json
import os
from datetime import datetime
from utils.user_database import db

# Procurar credentials.json em várias localizações
possible_paths = [
    os.path.join(os.path.dirname(__file__), "..", "config", "credentials.json"),
    os.path.join(os.path.dirname(__file__), "..", "credentials.json"),
    "credentials.json",
]

credentials_file = None
for path in possible_paths:
    if os.path.exists(path):
        credentials_file = path
        break

if not credentials_file:
    raise FileNotFoundError("Arquivo credentials.json não encontrado em nenhuma localização")

# Lê o usuário do arquivo credentials.json
with open(credentials_file, 'r', encoding='utf-8') as f:
    creds = json.load(f)

user_email = creds['login']

# Busca o user_id real pelo email
user = db.get_user_by_email(user_email)
if not user:
    raise Exception(f"Usuário com email {user_email} não encontrado!")
user_id = user['id']

def reset_daily_usage(user_id, date=None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    db.conn.execute(
        "DELETE FROM daily_usage WHERE user_id = ? AND usage_date = ?",
        [user_id, date]
    )
    print(f"Zerado uso diário para {user_id} ({user_email}) em {date}")

reset_daily_usage(user_id)
