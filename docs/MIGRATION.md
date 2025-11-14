# Guia de Migração de Dados

Este guia documenta os scripts de migração disponíveis no VibeCForms e como utilizá-los.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [CLI de Gerenciamento (manage.py)](#cli-de-gerenciamento-managepy)
3. [Scripts de Migração](#scripts-de-migração)
4. [Casos de Uso Comuns](#casos-de-uso-comuns)

---

## Visão Geral

O VibeCForms fornece ferramentas completas para migração e gerenciamento de dados:

- **manage.py**: CLI principal para operações administrativas
- **migrate_add_uuids.py**: Adiciona UUIDs a arquivos TXT existentes
- **migrate_sqlite_add_uuid.py**: Adiciona UUIDs a tabelas SQLite existentes
- **validate_fixes.py**: Valida integridade após migrações
- **test_insert.py**: Testa inserção de registros

---

## CLI de Gerenciamento (manage.py)

### Instalação

O `manage.py` está na raiz do projeto e já está pronto para uso:

```bash
chmod +x manage.py
```

### Comandos Disponíveis

#### 1. Listar Formulários

Lista todos os formulários cadastrados, seus backends e contagem de registros:

```bash
python manage.py list
```

**Saída:**
```
======================================================================
FORMULÁRIOS CADASTRADOS
======================================================================

📊 Total: 8 formulários

📄 contatos
   Título: Agenda Pessoal
   Backend: txt
   Registros: 24

📄 produtos
   Título: Catálogo de Produtos
   Backend: sqlite
   Registros: 17
...
```

---

#### 2. Status Detalhado

Exibe informações detalhadas sobre um formulário específico:

```bash
python manage.py status <form_path>
```

**Exemplo:**
```bash
python manage.py status contatos
```

**Saída:**
```
======================================================================
STATUS: contatos
======================================================================

📄 Título: Agenda Pessoal
📋 Campos: 3

🔧 Backend Atual: txt

📊 Estatísticas:
   Registros: 24
   Última atualização: 2025-11-14T22:05:49.303971
   Hash do schema: ee014237f822ba2d...

✅ Storage existe
   Registros atuais: 24
   Com UUID: 24/24
```

---

#### 3. Migrar Entre Backends

Migra dados de um backend para outro:

```bash
python manage.py migrate <form_path> --from <source> --to <target> [opções]
```

**Opções:**
- `--force`: Sobrescreve dados existentes no destino
- `--update-config`: Atualiza `persistence.json` com o novo backend
- `--yes` ou `-y`: Confirma automaticamente sem perguntar

**Exemplos:**

```bash
# Migrar contatos de TXT para SQLite
python manage.py migrate contatos --from txt --to sqlite

# Migrar produtos de SQLite para TXT (com confirmação automática)
python manage.py migrate produtos --from sqlite --to txt --yes

# Migrar e atualizar configuração permanente
python manage.py migrate contatos --from txt --to sqlite --update-config

# Forçar sobrescrita se destino já tiver dados
python manage.py migrate contatos --from txt --to sqlite --force
```

**Fluxo de Migração:**

1. Lê dados do backend de origem
2. Verifica se destino existe e tem dados
3. Solicita confirmação (a menos que `--yes`)
4. Cria storage de destino se não existir
5. Migra todos os registros (gera novos UUIDs)
6. Opcionalmente atualiza `persistence.json`

---

#### 4. Criar Backup

Cria backup manual de um formulário em formato JSON:

```bash
python manage.py backup <form_path>
```

**Exemplo:**
```bash
python manage.py backup contatos
```

**Saída:**
```
======================================================================
BACKUP: contatos
======================================================================

📊 Registros: 24

✅ Backup criado: data/backups/manual/contatos_20251114_201500.json
📦 24 registros salvos
```

**Formato do Backup:**
```json
{
  "form_path": "contatos",
  "spec": { ... },
  "records": [ ... ],
  "timestamp": "20251114_201500",
  "record_count": 24
}
```

---

#### 5. Validar Integridade

Valida integridade dos dados de um formulário:

```bash
python manage.py validate <form_path>
```

**Exemplo:**
```bash
python manage.py validate contatos
```

**Validações Realizadas:**

1. ✅ Verifica se todos os registros têm UUID
2. ✅ Detecta UUIDs duplicados
3. ✅ Valida campos obrigatórios

**Saída (sucesso):**
```
======================================================================
VALIDAÇÃO: contatos
======================================================================

📊 Total de registros: 24

✅ Validação bem-sucedida!
   Todos os registros estão íntegros
```

**Saída (problemas):**
```
⚠ 3 problemas encontrados:
   ⚠ 2 registros sem UUID
   ⚠ Registro 5: campo 'nome' obrigatório está vazio
```

---

## Scripts de Migração

### migrate_add_uuids.py

Adiciona UUIDs a arquivos TXT que não os possuem.

**Localização:** `scripts/migrate_add_uuids.py`

**Uso:**
```bash
# Dry-run (simula sem alterar)
python scripts/migrate_add_uuids.py --dry-run

# Executar migração
python scripts/migrate_add_uuids.py

# Migrar apenas um arquivo específico
python scripts/migrate_add_uuids.py --file data/txt/contatos.txt

# Especificar diretório
python scripts/migrate_add_uuids.py --path data/txt
```

**O que faz:**

1. Varre todos os `.txt` em `data/txt/`
2. Identifica registros sem UUID (formato antigo)
3. Gera UUID Crockford Base32 para cada registro
4. Cria backup automático antes de modificar
5. Atualiza arquivos com UUIDs

**Saída:**
```
======================================================================
MIGRAÇÃO: Adicionar UUIDs a Registros Existentes
======================================================================

📁 Arquivos a processar: 8

📄 Processando: contatos.txt
  📊 23 de 23 registros precisam de UUID
  ✓ Backup criado: data/backups/uuid_migration/contatos.txt.20251114_201917.backup
  ✓ Arquivo atualizado com sucesso!

======================================================================
✓ Migração concluída: 8/8 arquivos processados
======================================================================
```

---

### migrate_sqlite_add_uuid.py

Adiciona coluna `record_id` a tabelas SQLite existentes.

**Localização:** `scripts/migrate_sqlite_add_uuid.py`

**Uso:**
```bash
# Dry-run
python scripts/migrate_sqlite_add_uuid.py --dry-run

# Executar migração
python scripts/migrate_sqlite_add_uuid.py

# Especificar banco de dados
python scripts/migrate_sqlite_add_uuid.py --database data/sqlite/vibecforms.db
```

**O que faz:**

1. Conecta ao banco SQLite
2. Lista todas as tabelas (exceto `sqlite_*` e `tags`)
3. Verifica se cada tabela tem coluna `record_id`
4. Adiciona coluna se não existir
5. Popula com UUIDs para registros existentes
6. Cria índice único

**Saída:**
```
======================================================================
MIGRAÇÃO SQLite: Adicionar record_id às Tabelas
======================================================================

📁 Banco de dados: data/sqlite/vibecforms.db

💾 Criando backup...
  ✓ Backup criado: data/backups/sqlite_uuid_migration/vibecforms.db.20251114_211941.backup

📊 Tabelas a processar: 3

📄 Processando tabela: contatos
  📝 Adicionando coluna record_id...
  📝 Criando índice único...
  ✓ Coluna record_id adicionada
  📊 23 registros precisam de UUID
  ✓ 23 registros atualizados com UUID

======================================================================
✓ Migração concluída: 3/3 tabelas processadas
======================================================================
```

---

### validate_fixes.py

Valida correções críticas após migrações.

**Localização:** `scripts/validate_fixes.py`

**Uso:**
```bash
python scripts/validate_fixes.py
```

**Testes Realizados:**

1. ✅ UUIDs em registros pré-existentes
2. ✅ Inserir registro preserva existentes
3. ✅ Editar registro preserva outros
4. ✅ Deletar remove apenas alvo

**Saída:**
```
======================================================================
VALIDAÇÃO DAS CORREÇÕES CRÍTICAS
======================================================================

TESTE 1: Registros pré-existentes têm UUIDs
✓ SUCESSO: Todos os registros têm UUID!

TESTE 2: Inserir novo registro preserva registros existentes
✓ SUCESSO: Registro inserido sem deletar existentes!

...

RESULTADO FINAL: 4/4 testes passaram

🎉 TODAS AS CORREÇÕES VALIDADAS COM SUCESSO!
```

---

## Casos de Uso Comuns

### Caso 1: Migrar de TXT para SQLite

**Cenário:** Você tem um formulário em TXT e quer migrar para SQLite para melhor performance.

**Passo a passo:**

1. **Verificar estado atual:**
   ```bash
   python manage.py status contatos
   ```

2. **Criar backup:**
   ```bash
   python manage.py backup contatos
   ```

3. **Executar migração:**
   ```bash
   python manage.py migrate contatos --from txt --to sqlite --update-config
   ```

4. **Validar resultado:**
   ```bash
   python manage.py status contatos
   python manage.py validate contatos
   ```

5. **Testar via interface web:**
   - Acessar http://localhost:5000/contatos
   - Verificar que todos os registros aparecem
   - Adicionar/editar/deletar para confirmar que funciona

---

### Caso 2: Adicionar UUIDs a Dados Legados

**Cenário:** Você tem arquivos TXT antigos sem UUIDs e precisa atualizá-los.

**Passo a passo:**

1. **Simular migração (dry-run):**
   ```bash
   python scripts/migrate_add_uuids.py --dry-run
   ```

2. **Revisar o que será alterado:**
   - Verificar quantos arquivos serão processados
   - Confirmar quais registros precisam de UUID

3. **Executar migração:**
   ```bash
   python scripts/migrate_add_uuids.py
   ```

4. **Verificar backups:**
   ```bash
   ls data/backups/uuid_migration/
   ```

5. **Validar resultado:**
   ```bash
   python manage.py validate contatos
   ```

---

### Caso 3: Rollback de Migração

**Cenário:** Uma migração falhou ou produziu resultados inesperados.

**Passo a passo:**

1. **Localizar backup:**
   ```bash
   ls -lt data/backups/
   ```

2. **Para TXT - Restaurar arquivo:**
   ```bash
   cp data/backups/uuid_migration/contatos.txt.20251114_201917.backup data/txt/contatos.txt
   ```

3. **Para SQLite - Restaurar banco:**
   ```bash
   cp data/backups/sqlite_uuid_migration/vibecforms.db.20251114_211941.backup data/sqlite/vibecforms.db
   ```

4. **Para backup manual JSON - Restaurar via código:**
   ```python
   import json

   # Carregar backup
   with open('data/backups/manual/contatos_20251114_201500.json') as f:
       backup = json.load(f)

   # Restaurar dados usando o repositório
   from persistence.factory import RepositoryFactory
   repo = RepositoryFactory.get_repository('contatos')

   for record in backup['records']:
       repo.create('contatos', backup['spec'], record)
   ```

---

### Caso 4: Migração em Massa

**Cenário:** Migrar todos os formulários de TXT para SQLite.

**Script bash:**

```bash
#!/bin/bash

# Lista de formulários
FORMS=(
    "contatos"
    "produtos"
    "usuarios"
    "financeiro/contas"
    "financeiro/pagamentos"
    "rh/funcionarios"
)

# Migrar cada um
for form in "${FORMS[@]}"; do
    echo "Migrando $form..."
    python manage.py migrate "$form" --from txt --to sqlite --yes --update-config

    if [ $? -eq 0 ]; then
        echo "✓ $form migrado com sucesso"
    else
        echo "✗ Erro ao migrar $form"
        exit 1
    fi
done

echo "✅ Migração em massa concluída!"
```

---

### Caso 5: Auditoria de Dados

**Cenário:** Verificar integridade de todos os formulários.

**Script bash:**

```bash
#!/bin/bash

# Obter lista de formulários
FORMS=$(python manage.py list | grep "📄" | awk '{print $2}')

echo "Auditando formulários..."
echo ""

TOTAL=0
PASSED=0

for form in $FORMS; do
    ((TOTAL++))
    echo "Validando $form..."

    if python manage.py validate "$form" 2>&1 | grep -q "Validação bem-sucedida"; then
        echo "  ✓ OK"
        ((PASSED++))
    else
        echo "  ✗ Problemas encontrados"
    fi
    echo ""
done

echo "========================================"
echo "RESULTADO: $PASSED/$TOTAL formulários válidos"
echo "========================================"
```

---

## Boas Práticas

### Antes de Migrar

1. ✅ Sempre faça backup
2. ✅ Use `--dry-run` quando disponível
3. ✅ Valide o estado atual com `status`
4. ✅ Teste em ambiente de desenvolvimento primeiro

### Durante a Migração

1. ✅ Monitore a saída do script
2. ✅ Anote quaisquer erros ou warnings
3. ✅ Não interrompa migrações em andamento

### Após a Migração

1. ✅ Valide com `validate`
2. ✅ Teste CRUD via interface web
3. ✅ Verifique contagem de registros
4. ✅ Confirme que UUIDs foram gerados
5. ✅ Mantenha backups por pelo menos 7 dias

---

## Troubleshooting

### Problema: "Module not found"

**Solução:** Use `uv run python` em vez de `python`:
```bash
uv run python manage.py list
```

### Problema: "Permission denied"

**Solução:** Torne o script executável:
```bash
chmod +x manage.py
chmod +x scripts/migrate_add_uuids.py
```

### Problema: "Database is locked"

**Solução:** Feche todas as conexões ao banco:
```bash
# Pare o servidor Flask
pkill -f "uv run hatch run dev"

# Execute a migração
python manage.py migrate ...

# Reinicie o servidor
uv run hatch run dev
```

### Problema: "UUIDs duplicados"

**Solução:** Isso não deveria acontecer, mas se acontecer:
```bash
# Restaure do backup
cp data/backups/xxx.backup data/txt/form.txt

# Execute a migração novamente
python scripts/migrate_add_uuids.py --file data/txt/form.txt
```

---

## Referência Rápida

```bash
# Listar formulários
python manage.py list

# Status detalhado
python manage.py status <form>

# Migrar backend
python manage.py migrate <form> --from <src> --to <dst>

# Backup
python manage.py backup <form>

# Validar
python manage.py validate <form>

# Adicionar UUIDs (TXT)
python scripts/migrate_add_uuids.py

# Adicionar UUIDs (SQLite)
python scripts/migrate_sqlite_add_uuid.py

# Validar correções
python scripts/validate_fixes.py
```

---

## Suporte

Para problemas ou dúvidas:

1. Consulte a documentação em `docs/`
2. Verifique os logs de execução
3. Abra uma issue no repositório

---

**Última atualização:** 2025-11-14
**Versão:** 3.0.0-alpha
