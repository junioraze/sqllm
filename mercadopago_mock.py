#!/usr/bin/env python3
"""
Mock do MercadoPago para desenvolvimento
Simula todas as funcionalidades necessárias sem depender da API real
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class MockMercadoPago:
    """Mock completo da API do MercadoPago"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self._payments_db = {}  # Simula banco de dados de pagamentos
        self._preferences_db = {}  # Simula banco de dados de preferências
        
    class preference:
        @staticmethod
        def create(preference_data: Dict) -> Dict:
            """Simula criação de preferência de pagamento"""
            pref_id = f"mock_pref_{uuid.uuid4().hex[:8]}"
            
            mock_preference = {
                "id": pref_id,
                "init_point": f"https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id={pref_id}",
                "sandbox_init_point": f"https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id={pref_id}",
                "items": preference_data.get("items", []),
                "payer": preference_data.get("payer", {}),
                "external_reference": preference_data.get("external_reference"),
                "notification_url": preference_data.get("notification_url"),
                "back_urls": preference_data.get("back_urls", {}),
                "auto_return": preference_data.get("auto_return", "approved"),
                "date_created": datetime.now().isoformat(),
                "expires": True,
                "expiration_date_from": datetime.now().isoformat(),
                "expiration_date_to": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            # Simula resposta da API
            return {
                "status": 201,
                "response": mock_preference
            }
    
    class payment:
        @staticmethod
        def get(payment_id: str) -> Dict:
            """Simula consulta de pagamento"""
            # Status aleatório para simular diferentes cenários
            status_options = ["approved", "pending", "rejected", "cancelled"]
            weights = [0.7, 0.15, 0.10, 0.05]  # 70% aprovados, 15% pendentes, etc.
            
            status = random.choices(status_options, weights=weights)[0]
            
            mock_payment = {
                "id": payment_id,
                "status": status,
                "status_detail": "accredited" if status == "approved" else "pending_waiting_payment",
                "transaction_amount": random.choice([29.90, 59.90, 199.90]),
                "currency_id": "BRL",
                "date_created": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "date_approved": datetime.now().isoformat() if status == "approved" else None,
                "payer": {
                    "email": "usuario@teste.com",
                    "identification": {
                        "type": "CPF",
                        "number": "12345678901"
                    }
                },
                "payment_method_id": "visa",
                "payment_type_id": "credit_card",
                "external_reference": f"sub_{uuid.uuid4().hex[:8]}",
                "description": "Assinatura Premium - Análise de Dados"
            }
            
            return {
                "status": 200,
                "response": mock_payment
            }
        
        @staticmethod
        def search(filters: Dict) -> Dict:
            """Simula busca de pagamentos"""
            # Gera pagamentos mock baseado nos filtros
            results = []
            for i in range(random.randint(1, 5)):
                payment_id = f"mock_pay_{uuid.uuid4().hex[:8]}"
                results.append({
                    "id": payment_id,
                    "status": random.choice(["approved", "pending", "rejected"]),
                    "transaction_amount": random.choice([29.90, 59.90, 199.90]),
                    "date_created": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "external_reference": filters.get("external_reference", f"sub_{uuid.uuid4().hex[:8]}")
                })
            
            return {
                "status": 200,
                "response": {
                    "paging": {
                        "total": len(results),
                        "limit": 50,
                        "offset": 0
                    },
                    "results": results
                }
            }

class MockSDK:
    """Mock principal que simula o SDK do MercadoPago"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.preference = MockMercadoPago.preference()
        self.payment = MockMercadoPago.payment()
    
    def set_access_token(self, token: str):
        """Define o token de acesso"""
        self.access_token = token
        
    def simulate_webhook_notification(self, payment_id: str = None) -> Dict:
        """Simula notificação de webhook"""
        if not payment_id:
            payment_id = f"mock_pay_{uuid.uuid4().hex[:8]}"
            
        return {
            "id": random.randint(10000, 99999),
            "live_mode": False,
            "type": "payment",
            "date_created": datetime.now().isoformat(),
            "application_id": "123456789",
            "user_id": "123456",
            "version": 1,
            "api_version": "v1",
            "action": "payment.updated",
            "data": {
                "id": payment_id
            }
        }

# Simula dados de planos disponíveis
MOCK_PLANS = {
    "free": {
        "id": "free",
        "name": "Gratuito",
        "price": 0.00,
        "description": "Plano gratuito com 10 consultas/dia",
        "features": [
            "10 consultas por dia",
            "Interface básica",
            "Suporte da comunidade"
        ],
        "query_limit": 10,
        "priority_support": False
    },
    "basic": {
        "id": "basic",
        "name": "Básico",
        "price": 29.90,
        "description": "Acesso básico com 50 consultas/mês",
        "features": [
            "50 consultas por mês",
            "Relatórios básicos",
            "Suporte por email"
        ],
        "query_limit": 50,
        "priority_support": False
    },
    "premium": {
        "id": "premium", 
        "name": "Premium",
        "price": 59.90,
        "description": "Acesso premium com 200 consultas/mês",
        "features": [
            "200 consultas por mês",
            "Relatórios avançados",
            "Suporte prioritário",
            "Exportação de dados"
        ],
        "query_limit": 200,
        "priority_support": True
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise", 
        "price": 199.90,
        "description": "Acesso empresarial ilimitado",
        "features": [
            "Consultas ilimitadas",
            "Relatórios personalizados",
            "Suporte 24/7",
            "API dedicada",
            "Integração customizada"
        ],
        "query_limit": -1,  # -1 = ilimitado
        "priority_support": True
    }
}

def get_mock_sdk():
    """Retorna instância do SDK mock"""
    return MockSDK()

def simulate_payment_flow(plan_id: str, user_email: str) -> Dict:
    """Simula fluxo completo de pagamento"""
    sdk = get_mock_sdk()
    
    # 1. Cria preferência
    preference_data = {
        "items": [{
            "title": MOCK_PLANS[plan_id]["name"],
            "quantity": 1,
            "unit_price": MOCK_PLANS[plan_id]["price"]
        }],
        "payer": {"email": user_email},
        "external_reference": f"sub_{plan_id}_{uuid.uuid4().hex[:8]}"
    }
    
    preference = sdk.preference.create(preference_data)
    
    # 2. Simula pagamento (70% chance de sucesso)
    payment_success = random.random() < 0.7
    
    if payment_success:
        payment_id = f"mock_pay_{uuid.uuid4().hex[:8]}"
        payment = sdk.payment.get(payment_id)
        
        return {
            "success": True,
            "preference": preference,
            "payment": payment,
            "subscription_id": f"sub_{uuid.uuid4().hex[:8]}",
            "plan": MOCK_PLANS[plan_id]
        }
    else:
        return {
            "success": False,
            "preference": preference,
            "error": "Pagamento recusado - cartão insuficiente",
            "plan": MOCK_PLANS[plan_id]
        }

# Função para facilitar testes
def test_mock_functionality():
    """Testa todas as funcionalidades do mock"""
    print("🧪 Testando Mock do MercadoPago...")
    
    sdk = get_mock_sdk()
    
    # Teste 1: Criar preferência
    pref = sdk.preference.create({
        "items": [{"title": "Teste", "quantity": 1, "unit_price": 29.90}],
        "payer": {"email": "test@test.com"}
    })
    print(f"✅ Preferência criada: {pref['response']['id']}")
    
    # Teste 2: Consultar pagamento
    payment = sdk.payment.get("test_payment_123")
    print(f"✅ Pagamento consultado: {payment['response']['status']}")
    
    # Teste 3: Simular fluxo completo
    flow = simulate_payment_flow("premium", "usuario@teste.com")
    print(f"✅ Fluxo simulado: {'Sucesso' if flow['success'] else 'Falhou'}")
    
    print("🎉 Todos os testes do mock funcionando!")

if __name__ == "__main__":
    test_mock_functionality()