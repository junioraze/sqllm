import json
from datetime import datetime
from user_database import db

# Lê o usuário do arquivo credentials.json
with open('credentials.json', 'r', encoding='utf-8') as f:
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
