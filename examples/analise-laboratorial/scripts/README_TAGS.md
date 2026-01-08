# Populacao de Tags Kanban - Sistema LIMS

## Visao Geral

Script Python para criar e popular a tabela `tags` nos 4 workflows Kanban do sistema de analise laboratorial:

1. **Orcamento** (4 estados)
2. **Amostra** (3 estados)
3. **Resultado** (3 estados)
4. **Laudo** (4 estados)

## Estrutura da Tabela Tags

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_name TEXT NOT NULL,        -- Nome da entidade (orcamento, amostra, resultado, laudo)
    object_id TEXT NOT NULL,          -- ID do registro (ex: orcamento_1, amostra_2)
    tag TEXT NOT NULL,                -- Estado/tag (rascunho, enviado, aprovado, etc)
    applied_at DATETIME,              -- Timestamp de quando a tag foi aplicada
    applied_by TEXT,                  -- Usuario/sistema que aplicou a tag
    UNIQUE(object_name, object_id, tag)
)
```

## Workflows e Estados Populados

### 1. Orcamento (4 Estados)
| ID | Estado | Cor |
|----|--------|-----|
| orcamento_1 | rascunho | #6c757d (Cinza) |
| orcamento_2 | enviado | #17a2b8 (Azul Claro) |
| orcamento_3 | aprovado | #28a745 (Verde) |
| orcamento_4 | em_andamento | #007bff (Azul) |

### 2. Amostra (3 Estados, 4 Registros)
| ID | Estado |
|----|--------|
| amostra_1 | aguardando |
| amostra_2 | recebida |
| amostra_3 | fracionada |
| amostra_4 | recebida |

### 3. Resultado (3 Estados, 4 Registros)
| ID | Estado |
|----|--------|
| resultado_1 | aguardando |
| resultado_2 | em_execucao |
| resultado_3 | concluida |
| resultado_4 | em_execucao |

### 4. Laudo (4 Estados)
| ID | Estado |
|----|--------|
| laudo_1 | rascunho |
| laudo_2 | revisao |
| laudo_3 | liberado |
| laudo_4 | entregue |

## Como Usar

### Executar o Script

```bash
python3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/populate_tags.py
```

### Output Esperado

```
Criando/Populando tags Kanban para sistema LIMS
Banco de dados: /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db

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
```

## Validar os Dados

### Ver Todas as Tags
```bash
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT * FROM tags ORDER BY object_name, object_id;"
```

### Contar Tags por Workflow
```bash
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT object_name, COUNT(*) FROM tags GROUP BY object_name;"
```

### Ver Distribuicao de Tags por Estado
```bash
sqlite3 /home/rodrigo/VibeCForms/examples/analise-laboratorial/data/sqlite/lims.db \
  "SELECT object_name, tag, COUNT(*) FROM tags GROUP BY object_name, tag ORDER BY object_name, tag;"
```

## Estatísticas

**Total de Tags Criadas:** 16

**Por Workflow:**
- orcamento: 4 tags (4 estados diferentes)
- amostra: 4 tags (distribuído em 3 estados)
- resultado: 4 tags (distribuído em 3 estados)
- laudo: 4 tags (4 estados diferentes)

**Cobertura de Estados:**
- orcamento_1: rascunho
- orcamento_2: enviado
- orcamento_3: aprovado
- orcamento_4: em_andamento

- amostra_1: aguardando
- amostra_2: recebida
- amostra_3: fracionada
- amostra_4: recebida (duplicado para testar distribuição)

- resultado_1: aguardando
- resultado_2: em_execucao
- resultado_3: concluida
- resultado_4: em_execucao (duplicado para testar distribuição)

- laudo_1: rascunho
- laudo_2: revisao
- laudo_3: liberado
- laudo_4: entregue

## Arquivo do Script

**Localização:** `/home/rodrigo/VibeCForms/examples/analise-laboratorial/scripts/populate_tags.py`

**Funcionalidades:**
- Cria tabela `tags` se nao existir
- Popula com dados de 16 registros distribuídos em 4 workflows
- Trata duplicatas gracefully (skip com mensagem)
- Gera resumo de inserção e validação
- Exibe estatísticas de distribuição de tags

## Notas Importantes

1. **Idempotente:** O script pode ser executado multiplas vezes sem causar problemas (duplicatas sao ignoradas)
2. **Transações:** Todas as operacoes sao commitadas automaticamente
3. **Timestamps:** Usa `applied_at` com ISO format para rastreabilidade
4. **applied_by:** Todos sao marcados como "sistema" na populacao inicial
5. **Unicidade:** Constraint UNIQUE previne duplicatas (object_name, object_id, tag)

## Integracao com Kanban

As tags criadas servem como base para os Kanbans visuais:

1. Cada coluna do Kanban corresponde a uma `tag`
2. Os cards sao os registros com IDs como orcamento_1, amostra_2, etc
3. Mover um card entre colunas = remover tag antiga + adicionar tag nova
4. A tabela `tags` é a fonte de verdade para o estado dos registros

Exemplo de transição em Kanban:
- Card "orcamento_1" estava em "rascunho"
- Usuario arrasta para coluna "enviado"
- Sistema: `DELETE FROM tags WHERE object_id='orcamento_1' AND tag='rascunho'`
- Sistema: `INSERT INTO tags (object_name, object_id, tag, ...) VALUES ('orcamento', 'orcamento_1', 'enviado', ...)`

