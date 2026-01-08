# Quick Start - Tags Kanban Sistema LIMS

## Visao Geral em 60 Segundos

Este documento descreve a implementacao da funcionalidade de tags Kanban para o sistema LIMS, que permite rastrear o estado de orçamentos, amostras, resultados e laudos através de uma tabela SQLite.

## Arquivos Criados

```
/home/rodrigo/VibeCForms/examples/analise-laboratorial/
├── scripts/
│   ├── populate_tags.py          (Script de populacao)
│   ├── validate_tags.py          (Script de validacao)
│   └── README_TAGS.md            (Documentacao tecnica)
├── TAGS_IMPLEMENTATION.md        (Documentacao executiva)
└── QUICK_START.md               (Este arquivo)
```

## Banco de Dados

**Arquivo:** `/home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db`

**Tabela:** `tags` (16 registros)

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_name TEXT NOT NULL,       -- orcamento, amostra, resultado, laudo
    object_id TEXT NOT NULL,         -- orcamento_1, amostra_2, resultado_3, laudo_4
    tag TEXT NOT NULL,               -- rascunho, enviado, aprovado, em_andamento, etc
    applied_at DATETIME,             -- Timestamp de quando foi aplicado
    applied_by TEXT,                 -- Usuario ou 'sistema'
    UNIQUE(object_name, object_id, tag)
)
```

## Dados Populados - Distribuicao

### Workflow: Orcamento (4 Estados, 4 Registros)
```
Rascunho       ← orcamento_1
   ↓
Enviado        ← orcamento_2
   ↓
Aprovado       ← orcamento_3
   ↓
Em Andamento   ← orcamento_4
```

### Workflow: Amostra (3 Estados, 4 Registros)
```
Aguardando   ← amostra_1
Recebida     ← amostra_2, amostra_4
Fracionada   ← amostra_3
```

### Workflow: Resultado (3 Estados, 4 Registros)
```
Aguardando    ← resultado_1
Em Execucao   ← resultado_2, resultado_4
Concluida     ← resultado_3
```

### Workflow: Laudo (4 Estados, 4 Registros)
```
Rascunho   ← laudo_1
Revisao    ← laudo_2
Liberado   ← laudo_3
Entregue   ← laudo_4
```

## Como Usar

### 1. Executar Script de Populacao
```bash
python3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/populate_tags.py
```

Output esperado:
```
Criando/Populando tags Kanban para sistema LIMS
✓ Conectado ao banco de dados
✓ Tabela 'tags' criada/verificada com sucesso

Populando tags:
  ✓ orcamento  | orcamento_1  | rascunho        | inserted
  ✓ orcamento  | orcamento_2  | enviado         | inserted
  ...

Resumo de Populacao:
  Inseridas: 16 tags
  Duplicadas (skip): 0 tags
  Total: 16 tags processadas

Validacao - Total de tags: 16
✓ Script concluído com sucesso!
```

### 2. Validar Tags
```bash
python3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/validate_tags.py
```

Output:
```
✓ Tabela 'tags' existe
✓ Total de tags: 16
✓ Todos os workflows possuem cobertura de estados!

DETALHES POR WORKFLOW:
- amostra: 4 tags (aguardando, fracionada, recebida)
- laudo: 4 tags (entregue, liberado, rascunho, revisao)
- orcamento: 4 tags (aprovado, em_andamento, enviado, rascunho)
- resultado: 4 tags (aguardando, concluida, em_execucao)
```

### 3. Consultar via SQLite
```bash
# Ver todas as tags
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT * FROM tags ORDER BY object_name, object_id;"

# Contar por workflow
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT object_name, COUNT(*) FROM tags GROUP BY object_name;"

# Ver distribuicao de estados
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT object_name, tag, COUNT(*) FROM tags GROUP BY object_name, tag;"
```

## Integracao com Kanban Visual

### Arquitetura
- **Colunas Kanban** = Tags (rascunho, enviado, aprovado, etc)
- **Cards** = Registros (orcamento_1, amostra_2, resultado_3, laudo_4)
- **Movimentacao** = Transicao de tags

### Fluxo de Transicao
Quando usuario arrasta um card entre colunas:

1. **Frontend:** Detecta movimento do card
2. **API:** Envia request: `POST /api/kanban/move` com {object_id, from_tag, to_tag}
3. **Backend:** Executa transacao:
   ```sql
   BEGIN;
   DELETE FROM tags WHERE object_id='orcamento_1' AND tag='rascunho';
   INSERT INTO tags (object_name, object_id, tag, applied_by) 
   VALUES ('orcamento', 'orcamento_1', 'enviado', 'username');
   COMMIT;
   ```
4. **Frontend:** Atualiza visualizacao do board

## Exemplo de Queries para Kanban

```sql
-- Listar cards em uma coluna especifica
SELECT object_id FROM tags 
WHERE object_name='orcamento' AND tag='em_andamento';

-- Contar cards por coluna
SELECT tag, COUNT(*) as qty FROM tags 
WHERE object_name='orcamento' 
GROUP BY tag 
ORDER BY tag;

-- Historico de transicoes de um card
SELECT tag, applied_at, applied_by FROM tags 
WHERE object_name='orcamento' AND object_id='orcamento_1'
ORDER BY applied_at DESC;

-- Encontrar cards que nao mudaram de estado
SELECT object_id FROM tags 
WHERE object_name='amostra' AND tag='aguardando'
AND applied_at < datetime('now', '-7 days');
```

## Estrutura de Diretorio

```
/home/rodrigo/VibeCForms/examples/analise-laboratorial/
│
├── scripts/
│   ├── populate_tags.py           # Cria e popula tabela tags
│   ├── validate_tags.py           # Valida integridade
│   ├── README_TAGS.md             # Documentacao detalhada
│   ├── fix_schema_mismatch.py     # Utilitario existente
│   └── populate_database.py       # Utilitario existente
│
├── data/
│   └── sqlite/
│       └── lims.db                # Banco com tabela tags
│
├── config/
│   ├── kanban_boards.json         # Definicoes dos Kanbans
│   └── schema_history.json        # Historico de schemas
│
├── specs/
│   ├── orcamento.json             # Form spec
│   ├── amostra.json
│   ├── resultado.json
│   └── laudo.json
│
├── TAGS_IMPLEMENTATION.md         # Documentacao executiva
└── QUICK_START.md                 # Este arquivo
```

## Checklists

### Validacao da Implementacao
- [x] Tabela `tags` criada com schema correto
- [x] 16 tags populadas (4 por workflow)
- [x] Todos os 4 workflows cobertos (orcamento, amostra, resultado, laudo)
- [x] Todos os estados cobertos (100% coverage)
- [x] UNIQUE constraint implementado
- [x] Timestamps e applied_by preenchidos
- [x] Scripts de validacao passam com sucesso
- [x] Documentacao completa

### Proximas Implementacoes
- [ ] Integrar com controllers Kanban
- [ ] Implementar API endpoints para mover cards
- [ ] Adicionar auditoria (rastrear usuario)
- [ ] Criar historico de transicoes
- [ ] Implementar notificacoes
- [ ] Dashboard com analytics

## Troubleshooting

### Script retorna erro de banco nao encontrado
```bash
# Certifique-se que o caminho existe
ls -la /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db

# Se nao existir, crie o diretorio
mkdir -p /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/
```

### Script retorna "tabela ja existe"
Isso e normal! O script e idempotente:
```bash
# Voce pode rodar novamente sem problemas
python3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/populate_tags.py
```

### Validacao mostra "FALTAM estados"
Isso significa que alguns estados esperados nao foram populados:
```bash
# Verifique os dados
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT * FROM tags;"

# Se necessario, apague e repopule
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "DROP TABLE tags;"

# Repopule
python3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/populate_tags.py
```

## Referencia de Estados

### Orcamento States (4)
- `rascunho` - Estado inicial
- `enviado` - Enviado para cliente
- `aprovado` - Aprovado pelo cliente
- `em_andamento` - Amostras em coleta/analise

### Amostra States (3)
- `aguardando` - Aguardando recebimento
- `recebida` - Recebida no laboratorio
- `fracionada` - Fracionada para analises

### Resultado States (3)
- `aguardando` - Aguardando inicio de analise
- `em_execucao` - Analise em progresso
- `concluida` - Analise concluida

### Laudo States (4)
- `rascunho` - Laudo em preparacao
- `revisao` - Em revisao tecnica
- `liberado` - Liberado para entrega
- `entregue` - Entregue ao cliente

## Documentacao Relacionada

- `/home/rodrigo/VibeCForms/examples/analise-laboratorial/TAGS_IMPLEMENTATION.md` - Documentacao completa
- `/home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/README_TAGS.md` - Documentacao tecnica
- `/home/rodrigo/VibeCForms/examples/analise-laboratorial/config/kanban_boards.json` - Configuracao dos boards

## Suporte

Para duvidas:
1. Consulte `TAGS_IMPLEMENTATION.md` para visao executiva
2. Consulte `scripts/README_TAGS.md` para detalhes tecnicos
3. Execute `validate_tags.py` para diagnosticar problemas
4. Revise o script `populate_tags.py` para entender a logica

