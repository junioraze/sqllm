# Git Pull Seguro

Ferramenta para atualizar repositórios preservando arquivos de configuração local.

## Como funciona

1. **Detecta** arquivos locais (gl.json, credentials.json, tables_config.json, etc)
2. **Salva** em pasta temporária
3. **Executa** git pull normalmente
4. **Restaura** arquivos no lugar certo

## Uso

### Simular (DRY RUN)
```bash
cd /home/Junio/seu_projeto
python ../gl_sqllm/tools/git_pull_safe.py . --dry-run
```

### Atualizar de verdade
```bash
python ../gl_sqllm/tools/git_pull_safe.py .
```

### Ver quais arquivos tem
```bash
python ../gl_sqllm/tools/check_config.py /home/Junio/seu_projeto
```

## Arquivos protegidos

- gl.json (credenciais Google)
- credentials.json (credenciais app)
- tables_config.json (tabelas)
- client_config.json (UI)
- .env (variáveis)

Esses arquivos **nunca** são deletados ou sobrescritos.

## Exemplo prático

```bash
# 1. Entrar no projeto
cd /home/Junio/ap_sqllm

# 2. Simular
python ../gl_sqllm/tools/git_pull_safe.py . --dry-run

# 3. Se OK, atualizar
python ../gl_sqllm/tools/git_pull_safe.py .

# 4. Pronto!
```
