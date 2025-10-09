# MODO EMPRESARIAL - SISTEMA SIMPLIFICADO COM LIMITE

## Configuração Implementada

### 🔧 **Contr### 🎯 **Simplicidade**
- Login com credenciais empresariais
- Interface limpa sem aba de cadastro
- Foco total na funcionalidade principal

### 📊 **Controle Adequado**
- Limite de 100 consultas por dia
- Monitoramento discreto de uso
- Sem pressão comercial

### 🚀 **Experiência Streamlined**
- Usuário empresarial criado automaticamente
- Interface de login simplificada
- Funcionalidade completa disponível*
- **Arquivo**: `.env`
- **Variável**: `EMPRESARIAL=True`
- **Efeito**: Ativa modo empresarial quando `True`

### 🔐 **Sistema de Login**
- **No modo empresarial**: 
  - Mostra tela de login normal (SEM aba de cadastro)
  - Usuário empresarial criado automaticamente na primeira execução
  - Login manual na UI com credenciais do `credentials.json`
- **No modo normal**: Sistema completo de cadastro/login com duas abas

### 📊 **Limite de Uso**
- **Usuário empresarial**: 100 consultas por dia
- **Plano especial**: "Empresarial" criado automaticamente
- **Controle**: Limite aplicado mas interface simplificada

## Funcionalidades Modificadas

### 1. **Autenticação (`auth_system.py`)**
- **Modo Empresarial**:
  - Mostra tela de login (SEM aba de cadastro)
  - Usuário empresarial criado automaticamente na primeira execução
  - **Cria plano "Empresarial" com limite de 100 consultas/dia**
  - **Atribui plano empresarial automaticamente ao usuário**
  - Login manual com credenciais do `credentials.json`
- **Modo Normal**:
  - Sistema completo de autenticação
  - Tela de login/cadastro com duas abas

### 2. **Interface Principal (`main.py`)**
- **Seções omitidas no modo empresarial**:
  - ❌ Seção "💳 Assinatura" completa no sidebar
  - ❌ Botões de "Ver Planos" e "Upgrade"
  - ❌ Informações de preços e upgrades
  - ❌ Limite diário detalhado nas limitações do sistema

- **Seções mantidas no modo empresarial**:
  - ✅ Configurações de tema
  - ✅ Usuário e logout
  - ✅ **Indicador discreto de uso diário (simples)**
  - ✅ Funcionalidades principais do chat

### 3. **Verificação de Permissões**
- **Modo Empresarial**: 
  - ✅ **Verifica limite de 100 consultas/dia**
  - ❌ Não oferece upgrade quando limite atingido
  - ⚠️ Mensagem simples: "Limite diário atingido"
- **Modo Normal**: 
  - ✅ Verifica plano e limite diário
  - ✅ Oferece upgrade quando necessário

## Como Usar

### Para Ativar Modo Empresarial:
1. Editar `.env`: `EMPRESARIAL=True`
2. Configurar `credentials.json` com login/senha desejados
3. Reiniciar aplicação
4. **Sistema criará automaticamente plano com 100 consultas/dia**

### Para Ativar Modo Normal:
1. Editar `.env`: `EMPRESARIAL=False`
2. Reiniciar aplicação

## Credenciais Empresariais

**Arquivo**: `credentials.json`
```json
{
  "login": "conjecto@conjecto.com.br",
  "password": "app.viaquest"
}
```

### Comportamento:
- **Usuário criado automaticamente** no banco com esses dados
- **Plano "Empresarial" criado** com 100 consultas/dia
- **Login automático** sem interação do usuário
- **Sem cadastro manual** necessário

## Plano Empresarial Automático

### Especificações:
- **ID**: `empresarial`
- **Nome**: `Empresarial`
- **Limite diário**: 100 consultas
- **Preço**: R$ 0,00 (gratuito)
- **Features**: 100 consultas por dia, Acesso completo, Interface simplificada
- **Suporte prioritário**: Ativado

### Controle de Limite:
- **Aplicado**: Sim, 100 consultas por dia
- **Interface**: Indicador simples de uso no sidebar
- **Ao atingir limite**: Mensagem discreta, sem ofertas de upgrade
- **Reset**: Automático a cada dia

## Benefícios do Modo Empresarial

### 🎯 **Simplicidade**
- Acesso direto sem cadastro
- Interface limpa sem informações comerciais
- Foco total na funcionalidade principal

### � **Controle Adequado**
- Limite de 100 consultas por dia
- Monitoramento discreto de uso
- Sem pressão comercial

### �🚀 **Experiência Streamlined**
- Sem barreiras de entrada
- Sem preocupações de upgrade
- Funcionalidade completa disponível

### 🔒 **Gestão Controlada**
- Credenciais fixas e controladas
- Plano automático e transparente
- Fácil implantação em ambiente empresarial

## Status: ✅ IMPLEMENTADO

O sistema agora funciona em dois modos:
- **EMPRESARIAL=True**: Versão simplificada com limite de 100/dia
- **EMPRESARIAL=False**: Versão completa com planos e cadastro

**Limite aplicado, interface limpa e experiência empresarial otimizada!** 🎉