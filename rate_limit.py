import json
from datetime import datetime, timedelta
import os
from pathlib import Path

class RateLimiter:
    def __init__(self, max_requests_per_day=100, state_file='rate_limit_state.json'):
        self.max_requests = max_requests_per_day
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self):
        """Carrega o estado do rate limit do arquivo ou cria um novo"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    # Verifica se a data salva ainda é hoje
                    last_date = datetime.strptime(state['date'], '%Y-%m-%d').date()
                    if last_date == datetime.now().date():
                        return state
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Se não existir ou for de outro dia, cria novo estado
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'count': 0
        }

    def _save_state(self):
        """Salva o estado atual no arquivo"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def check_limit(self):
        """Verifica se o limite foi atingido"""
        current_date = datetime.now().date()
        saved_date = datetime.strptime(self.state['date'], '%Y-%m-%d').date()

        # Se for um novo dia, reinicia o contador
        if current_date != saved_date:
            self.state = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': 0
            }

        return self.state['count'] >= self.max_requests

    def increment(self):
        """Incrementa o contador de requisições"""
        current_date = datetime.now().date()
        saved_date = datetime.strptime(self.state['date'], '%Y-%m-%d').date()

        if current_date != saved_date:
            self.state = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': 1
            }
        else:
            self.state['count'] += 1

        self._save_state()