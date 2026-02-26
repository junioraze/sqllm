# 🔄 ATUALIZAÇÃO COM GIT PULL (Simples e Seguro)

## Entendimento

Cada projeto é um **repositório git independente**. Quando você faz `git pull`:

```
gl_sqllm/                      fa_sqllm/
├── git pull ✓                 ├── git pull ✓
├── código atualizado ✓        ├── código atualizado ✓
└── mas e as credenciais? ❌   └── credenciais específicas? ❌
```

**Problema:** Arquivos que não estão no git (credenciais, configs locais) podem:
- Ser deletados acidentalmente
- Ficar fora de sincronia
- Ser perdidos

**Solução:** Uma ferramenta que:
1. **Salva** arquivos locais antes de `git pull`
2. Executa **`git pull`**
3. **Restaura** arquivos locais (sem perder nem deletar)

---

## 📋 Arquivos Preservados

### Sempre Salvos (Nunca deletar!)

```
gl.json                         ← Google credentials (SECRETO!)
credentials.json                ← App credentials (SECRETO!)
config/tables_config.json       ← Tabelas do seu projeto
config/client_config.json       ← UI customizada
rate_limit_state.json           ← Estado local
cache.db                        ← Cache
```

**Regra de ouro:** Se não está no `git add`, não é sincronizado. Se não é sincronizado, não deve ser deletado.

---

## 🚀 Como Usar

### Listar arquivos que serão preservados

```bash
python tools/git_pull_safe.py --list-files
```

Output:
```
📋 ARQUIVOS QUE SERÃO PRESERVADOS:

  • gl.json
  • credentials.json
  • config/tables_config.json
  • config/client_config.json
  • rate_limit_state.json
  • cache.db
  • cache.ann
  • cache.meta.json
  • test_output_*.json
  • ... (mais 5 arquivos)
```

### Simular atualização (DRY RUN)

```bash
cd /home/Junio/fa_sqllm
python ../gl_sqllm/tools/git_pull_safe.py . --dry-run
```

Output:
```
======================================================================
GERENCIADOR DE GIT PULL
======================================================================
Projeto: fa_sqllm
Caminho: /home/Junio/fa_sqllm
Modo: DRY RUN (simulação)

1️⃣ Detectando arquivos locais...
   Encontrados: 5 arquivo(s)
      • gl.json
      • config/tables_config.json
      • rate_limit_state.json
      • cache.db
      • cache.ann

2️⃣ Salvando arquivos locais...
   [DRY] Salvaria 5 arquivo(s)

3️⃣ Executando git pull...
   [DRY] Executaria git pull

4️⃣ [DRY] Restauraria arquivos locais

======================================================================
✅ CONCLUÍDO COM SUCESSO!
======================================================================
```

### Executar atualização REAL

```bash
cd /home/Junio/fa_sqllm
python ../gl_sqllm/tools/git_pull_safe.py . 
```

O que acontece:
```
1️⃣ Salva: gl.json, config/tables_config.json, cache.db, etc
2️⃣ Executa: git pull (traz atualizações do repositório)
3️⃣ Restaura: Todos os arquivos locais voltam para o lugar
4️⃣ Pronto!
```

---

## 💡 Workflow Prático

### Scenario: Atualizar um projeto de produção

```bash
# 1. Entrar no projeto
cd /home/Junio/fa_sqllm

# 2. Ver o que seria atualizado (DRY RUN)
python ../gl_sqllm/tools/git_pull_safe.py . --dry-run

# 3. Se OK, atualizar REAL
python ../gl_sqllm/tools/git_pull_safe.py .

# 4. Verificar que tudo funcionou
python main.py
# ✓ Credenciais ainda existem
# ✓ Configs específicas do projeto ainda existem
# ✓ Código atualizado
```

### Scenario: Atualizar TODOS os projetos

```bash
# Criar um script rápido
for project in ap_sqllm av_sqllm cb_sqllm cm_sqllm fa_sqllm sa_sqllm sqllm tc_sqllm; do
    echo "Atualizando: $project"
    cd /home/Junio/$project
    python ../gl_sqllm/tools/git_pull_safe.py . --dry-run
    # Ver se ficou OK antes de executar
done
```

---

## ✅ O que é Preservado

```
✓ gl.json                       Credenciais Google (PROTEGIDO!)
✓ credentials.json              Credenciais App
✓ config/tables_config.json     Suas tabelas
✓ config/client_config.json     UI customizada
✓ rate_limit_state.json         Estado local
✓ cache.db                      Cache local
✓ cache.ann                     Embeddings
✓ .env                          Variáveis de ambiente
```

## ❌ O que é Atualizado (Git Pull)

```
✓ config/settings.py            Variáveis compartilhadas
✓ rag_system/manager.py         RAG Manager
✓ utils/logger.py               Logger
✓ generators/test_generator.py  Gerador
✓ README.md                      Documentação
✓ requirements.txt              Dependências
```

---

## 🔒 Segurança

### Confidencialidade
- ✅ Credenciais NUNCA são tocadas
- ✅ Chaves de API NUNCA são deletadas
- ✅ Tokens NUNCA são sobrescritos

### Integridade
- ✅ Arquivos locais SEMPRE são restaurados
- ✅ Nada é perdido
- ✅ Rollback automático se algo der errado

### Auditoria
- ✅ Lista de arquivos preservados é clara
- ✅ Logs mostram o que foi feito
- ✅ DRY RUN permite validar antes

---

## 🚨 Troubleshooting

### Problema: Git pull falhou

**Causa:** Conflitos de merge, problemas de conexão

**Solução:**
```bash
# Ver detalhes do erro
cd /home/Junio/fa_sqllm
git status
git pull  # Tentar novamente

# Se persistir, resolver conflito manualmente
git merge --abort  # Desfazer merge
```

### Problema: Arquivo local não foi restaurado

**Causa:** Disco cheio, permissão, arquivo corrompido no backup

**Verificar:**
```bash
# Ver se arquivo existe
ls -la /home/Junio/fa_sqllm/gl.json

# Se não existir, verificar backup
ls -la /tmp/  # Temp backups

# Restaurar manualmente
cp /path/backup /home/Junio/fa_sqllm/
```

### Problema: Tenho dúvida se funcionou

**Solução:** Usar DRY RUN primeiro!

```bash
# Sempre fazer DRY RUN antes
python tools/git_pull_safe.py . --dry-run

# Ver se logs mostram o que vai acontecer
# Se OK, executar para real
python tools/git_pull_safe.py .
```

---

## 📊 Comparação: Antes vs Depois

| Antes | Depois |
|-------|--------|
| ❌ `cd projeto && git pull` | ✅ `python git_pull_safe.py .` |
| ❌ Risco de perder credenciais | ✅ Credenciais sempre preservadas |
| ❌ Arquivos locais podem ser deletados | ✅ Arquivos locais sempre restaurados |
| ❌ Manual e arriscado | ✅ Automatizado e seguro |
| ❌ Sem auditoria | ✅ Logs claros do que foi feito |

---

## 🎯 Benefícios

### Para Você
- ✨ Uma linha para atualizar
- 🔒 Credenciais sempre seguras
- 📋 Arquivos locais nunca perdidos
- ✅ Simples e funciona

### Para o Time
- 🚀 Processo padronizado
- 📊 Logs auditáveis
- 🛡️ Seguro por padrão
- 🔄 DRY RUN antes de executar

---

## 📞 Comandos Rápidos

```bash
# Listar arquivos preservados
python tools/git_pull_safe.py --list-files

# Simular atualização
python tools/git_pull_safe.py /projeto/path --dry-run

# Atualizar REAL
python tools/git_pull_safe.py /projeto/path

# Usando caminho relativo
cd /home/Junio/fa_sqllm
python ../gl_sqllm/tools/git_pull_safe.py .
```

---

## ✨ Conclusão

**Simple & Safe:** Uma ferramenta que:
- Faz `git pull` de forma segura
- Preserva TODOS os arquivos locais
- Nunca deleta credenciais
- Uma linha para usar

**Pronto para produção!** 🚀

```bash
# Use assim
python tools/git_pull_safe.py /path/to/projeto
```
