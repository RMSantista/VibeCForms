# 📋 PLANO ARQUITETURAL: Tags as State + UUID Migration + Data Organization

**Data**: 2025-01-13
**Versão**: 1.0
**Status**: Em Implementação
**Arquiteto**: Claude Code + Skill Arquiteto

---

## 🎯 Visão Geral

Este plano implementa:
1. **Sistema de UUIDs Crockford Base32** (task-tag-as-state.md)
2. **Tags as State** (Convenção #4 do README.md)
3. **Reorganização da Arquitetura de Dados** (mover dados de `src/` para `data/`)
4. **Migração Segura de Dados Existentes** (TXT e SQLite)

**Filosofia**: Convention → Configuration → Code

---

## 📊 Análise do Estado Atual

### Dados Identificados:
- **SQLite**: `vibecforms.db` com 4 tabelas (contatos, produtos, financeiro_pagamentos, rh_departamentos_areas)
- **TXT**: 8 arquivos `.txt` em `src/`
- **IDs Atuais**: Integer auto-increment (SQLite) e índice posicional (TXT)

### Problemas Identificados (TECH_DEBT.md):
1. ❌ **IDs baseados em índice** - anti-pattern que impede tags e relacionamentos
2. ❌ **Tags as State não implementado** - core convention ausente
3. ❌ **Dados em `src/`** - violação de separação de responsabilidades

---

## 🏗️ ARQUITETURA PROPOSTA

### 1. Nova Estrutura de Diretórios

```
VibeCForms/
├── src/                          # Código-fonte APENAS
│   ├── VibeCForms.py
│   ├── persistence/
│   ├── services/                 # NOVO: Camada de serviços
│   │   └── tag_service.py
│   ├── utils/                    # NOVO: Utilitários
│   │   └── crockford.py
│   ├── templates/
│   ├── specs/
│   └── config/
│       ├── persistence.json
│       └── schema_history.json
├── data/                         # NOVO: Todos os dados aqui
│   ├── txt/                      # Dados TXT
│   │   ├── contatos.txt
│   │   ├── contatos_tags.txt
│   │   └── ...
│   ├── sqlite/                   # Bancos SQLite
│   │   └── vibecforms.db
│   └── backups/                  # Backups de migrações
│       └── migrations/
├── scripts/                      # Scripts de migração
│   ├── migrate_to_uuids.py
│   ├── migrate_data_folder.py
│   └── validate_migration.py
├── tests/
└── docs/
```

### 2. Sistema de IDs Crockford Base32

**Formato**: 27 caracteres (26 UUID + 1 check digit)
- **Exemplo**: `3HNMQR8PJSG0C9VWBYTE12K`
- **Character Set**: `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (32 símbolos, sem I, L, O, U)
- **Check Digit**: Módulo 32 (variação VibeCForms, não usa símbolos especiais)

**Benefícios**:
- ✅ URL-safe
- ✅ Humano-legível
- ✅ Detecção de erros
- ✅ Mais curto que UUID hex (27 vs 36 caracteres)

---

## 📅 PLANO DE IMPLEMENTAÇÃO (7 FASES)

### **FASE 0: Reorganização da Arquitetura de Dados** ⏱️ 1 dia

**Objetivo**: Mover todos os dados de `src/` para `data/` antes de qualquer migração de UUID.

#### 0.1 Criar Nova Estrutura de Diretórios
```bash
mkdir -p data/txt
mkdir -p data/sqlite
mkdir -p data/backups/migrations
```

#### 0.2 Criar Script de Migração de Diretórios
**Arquivo**: `scripts/migrate_data_folder.py`

**Responsabilidades**:
- Mover todos os arquivos `.txt` de `src/` para `data/txt/`
- Mover `vibecforms.db` de `src/` para `data/sqlite/`
- Mover backups de `src/backups/` para `data/backups/`
- Criar backup completo antes da migração
- Atualizar `persistence.json` com novos caminhos

#### 0.3 Atualizar Configuração
**Arquivo**: `src/config/persistence.json`

```json
{
  "default_backend": "txt",
  "data_root": "data",
  "backends": {
    "txt": {
      "type": "txt",
      "connection": {
        "directory": "data/txt",
        "encoding": "utf-8",
        "delimiter": ";"
      }
    },
    "sqlite": {
      "type": "sqlite",
      "connection": {
        "database": "data/sqlite/vibecforms.db",
        "timeout": 10
      }
    }
  },
  "backups": {
    "directory": "data/backups/migrations"
  }
}
```

#### 0.4 Atualizar Adapters
**Arquivos**: `src/persistence/adapters/txt_adapter.py`, `sqlite_adapter.py`

- Atualizar todos os caminhos para usar `data_root` da configuração
- Garantir que todos os métodos leiam de `data/txt/` e `data/sqlite/`

#### 0.5 Atualizar Referências no Código Principal
**Arquivo**: `src/VibeCForms.py`

- Buscar e substituir todos os caminhos hardcoded
- Atualizar variáveis de caminho para usar configuração

#### 0.6 Testes da Fase 0
- ✅ Todos os arquivos movidos para `data/`
- ✅ Aplicação inicia sem erros
- ✅ CRUD funciona normalmente
- ✅ Backup criado em `data/backups/`
- ✅ Nenhum arquivo `.txt` ou `.db` permanece em `src/`

**Critério de Sucesso**: ✅ Todos os testes existentes passam sem modificação

---

### **FASE 1: Implementar Sistema Crockford Base32** ⏱️ 2 dias

#### 1.1 Criar Módulo Crockford
**Arquivo**: `src/utils/crockford.py`

**Funções**:
```python
def encode_uuid(uuid_obj: UUID) -> str:
    """Encode UUID to 26-char Crockford Base32"""

def calculate_check_digit(encoded: str) -> str:
    """Calculate check digit (mod 32)"""

def generate_id() -> str:
    """Generate new 27-char ID (26 + check)"""

def validate_id(id_str: str) -> bool:
    """Validate format and checksum"""

def decode_id(id_str: str) -> UUID:
    """Decode to UUID (remove check digit first)"""
```

#### 1.2 Testes Unitários
**Arquivo**: `tests/test_crockford.py`

- Test encoding/decoding round-trip
- Test check digit calculation
- Test validation (valid/invalid IDs)
- Test case-insensitivity
- Test error detection (wrong checksum)

**Critério de Sucesso**: ✅ 15+ testes passando

---

### **FASE 2: Atualizar BaseRepository Interface** ⏱️ 1 dia

#### 2.1 Modificar Interface Base
**Arquivo**: `src/persistence/base.py`

**Mudanças**:
- REMOVER métodos baseados em índice
- ADICIONAR métodos baseados em ID
- ADICIONAR métodos de tags

---

### **FASE 3: Implementar Adapters com UUID** ⏱️ 3 dias

#### 3.1 TxtAdapter com UUID
**Arquivo**: `src/persistence/adapters/txt_adapter.py`

**Formato Novo**:
```
ID;nome;telefone;whatsapp
3HNMQR8PJSG0C9VWBYTE12K;Nicole Carvalho;+55 31 4736 1125;True
```

#### 3.2 SQLiteAdapter com UUID
**Arquivo**: `src/persistence/adapters/sqlite_adapter.py`

**Schema Novo**:
```sql
CREATE TABLE contatos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    whatsapp BOOLEAN
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    applied_by TEXT NOT NULL,
    metadata TEXT,
    UNIQUE(object_type, object_id, tag)
);
```

---

### **FASE 4: Scripts de Migração de Dados** ⏱️ 2 dias

#### 4.1 Migração SQLite
**Arquivo**: `scripts/migrate_sqlite_to_uuids.py`

#### 4.2 Migração TXT
**Arquivo**: `scripts/migrate_txt_to_uuids.py`

#### 4.3 Sincronização TXT-SQLite
**Arquivo**: `scripts/sync_txt_sqlite_ids.py`

---

### **FASE 5: Atualizar Application Layer** ⏱️ 2 dias

#### 5.1 Criar TagService
**Arquivo**: `src/services/tag_service.py`

#### 5.2 Atualizar Rotas em VibeCForms.py

---

### **FASE 6: Atualizar Templates** ⏱️ 1 dia

#### 6.1 Modificar form.html
#### 6.2 Modificar edit.html

---

### **FASE 7: Testes e Validação** ⏱️ 2 dias

#### 7.1 Atualizar Testes Existentes
#### 7.2 Novos Testes de Tags
#### 7.3 Testes de Migração
#### 7.4 Validação Manual

---

## 📝 ESTRATÉGIA DE MIGRAÇÃO DE DADOS

### Prioridades:
1. **SEGURANÇA MÁXIMA**: Múltiplos backups antes de qualquer mudança
2. **RASTREABILIDADE**: Logs detalhados de cada operação
3. **VALIDAÇÃO**: Verificações em cada etapa
4. **ROLLBACK**: Plano de reversão se algo falhar

### Ordem de Execução:

```
FASE 0: Reorganizar Dados (src → data)
  ↓
FASE 1: Implementar Crockford (utils)
  ↓
FASE 2: Atualizar BaseRepository
  ↓
FASE 3: Implementar Adapters
  ↓
FASE 4: Migrar Dados (CRÍTICO)
  ↓
FASE 5: Atualizar Application Layer
  ↓
FASE 6: Atualizar Templates
  ↓
FASE 7: Testes Completos
```

---

## 📊 MÉTRICAS DE SUCESSO

### Requisitos Obrigatórios:
- ✅ **100% dos dados migrados** (nenhum registro perdido)
- ✅ **Todos os IDs válidos** (formato Crockford + checksum correto)
- ✅ **Zero duplicação** de IDs
- ✅ **Dados em `data/`** (nenhum dado em `src/`)
- ✅ **Tags funcionais** em TXT e SQLite
- ✅ **Todos os testes passando** (40+ testes)
- ✅ **Backward compatibility = 0** (sem suporte a índices)

---

## 📅 CRONOGRAMA ESTIMADO

| Fase | Descrição | Duração | Status |
|------|-----------|---------|--------|
| 0 | Reorganizar Dados (src → data) | 1 dia | 🔄 Em Progresso |
| 1 | Implementar Crockford Utils | 2 dias | ⏳ Pendente |
| 2 | Atualizar BaseRepository | 1 dia | ⏳ Pendente |
| 3 | Implementar Adapters (UUID + Tags) | 3 dias | ⏳ Pendente |
| 4 | Migração de Dados (CRÍTICO) | 2 dias | ⏳ Pendente |
| 5 | Atualizar Application Layer | 2 dias | ⏳ Pendente |
| 6 | Atualizar Templates | 1 dia | ⏳ Pendente |
| 7 | Testes e Validação | 2 dias | ⏳ Pendente |

**TOTAL**: **14 dias úteis** (~3 semanas)

---

## 🎯 DELIVERABLES

### Código (8 arquivos novos):
1. ✅ `src/utils/crockford.py`
2. ✅ `src/services/tag_service.py`
3. ✅ `scripts/migrate_data_folder.py`
4. ✅ `scripts/migrate_sqlite_to_uuids.py`
5. ✅ `scripts/migrate_txt_to_uuids.py`
6. ✅ `scripts/sync_txt_sqlite_ids.py`
7. ✅ `scripts/validate_migration.py`

### Código (modificações):
1. ✅ `src/persistence/base.py`
2. ✅ `src/persistence/adapters/txt_adapter.py`
3. ✅ `src/persistence/adapters/sqlite_adapter.py`
4. ✅ `src/VibeCForms.py`
5. ✅ `src/templates/form.html`
6. ✅ `src/templates/edit.html`
7. ✅ `src/config/persistence.json`

### Testes (45+ novos):
1. ✅ `tests/test_crockford.py` (15+ testes)
2. ✅ `tests/test_tags.py` (20+ testes)
3. ✅ `tests/test_migration.py` (10+ testes)
4. ✅ Atualização de `tests/test_form.py`

### Documentação:
1. ✅ `docs/crockford_ids.md`
2. ✅ `docs/tags_guide.md`
3. ✅ `docs/migration_guide.md`
4. ✅ Atualização de `README.md`
5. ✅ Atualização de `TECH_DEBT.md`
6. ✅ Atualização de `docs/prompts.md`

---

## 🔄 PROCESSO DE DESENVOLVIMENTO

Cada fase segue o ciclo:

1. **Codificar** → Implementar funcionalidade
2. **Testar** → Criar/executar testes específicos
3. **Corrigir** → Resolver erros encontrados
4. **Revisar** → Verificar qualidade do código
5. **Testar Geral** → Executar TODOS os testes (100% pass)
6. **Homologar** → Revisão humana
7. **Aprovar** → Marcar como concluída
8. **Documentar** → Atualizar docs relevantes
9. **Commit** → Formatar, commitar e push

---

## 📚 DOCUMENTOS A ATUALIZAR (Por Fase)

### Fase 0:
- `docs/prompts.md` - Adicionar este planejamento
- `docs/planning/workflow/essential/tags-as-state-uuid-migration-plan.md` - Este arquivo

### Fase 1:
- `docs/crockford_ids.md` - Criar documentação do sistema de IDs

### Fase 2-3:
- `ARCHITECTURE.md` - Atualizar com nova interface de repositório

### Fase 4:
- `docs/migration_guide.md` - Criar guia de migração

### Fase 5-6:
- `README.md` - Atualizar status da Convenção #4
- `CLAUDE.md` - Atualizar com novas convenções

### Fase 7:
- `TECH_DEBT.md` - Marcar itens 1, 4, 5 como completos
- `docs/tags_guide.md` - Criar guia de uso de tags

---

## ⚠️ RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Perda de dados na migração | Baixa | Alto | Múltiplos backups automáticos |
| IDs duplicados | Média | Alto | Validação em cada etapa |
| Testes não passam após mudanças | Alta | Médio | Atualizar testes incrementalmente |
| Performance degradada | Baixa | Médio | Benchmarks antes/depois |
| Incompatibilidade TXT-SQLite | Média | Alto | Script de sincronização dedicado |

---

## ✅ CRITÉRIOS DE ACEITAÇÃO FINAL

- [ ] Zero arquivos de dados em `src/`
- [ ] Todos os dados em `data/txt/` e `data/sqlite/`
- [ ] 100% dos registros migrados (count validado)
- [ ] Todos os IDs são Crockford válidos (27 chars)
- [ ] Zero IDs duplicados
- [ ] Tags funcionam (add, remove, query)
- [ ] Todos os testes passam (40+ testes)
- [ ] Aplicação roda sem erros
- [ ] CRUD completo funcional
- [ ] Documentação atualizada
- [ ] Código formatado (ruff/black)
- [ ] Git commit com mensagem descritiva
- [ ] Push para GitHub bem-sucedido

---

**Gerado por**: Claude Code + Skill Arquiteto
**Data**: 2025-01-13
**Versão**: 1.0
