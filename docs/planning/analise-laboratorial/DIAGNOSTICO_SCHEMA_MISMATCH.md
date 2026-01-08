# Diagnóstico: Schema Mismatch

## Problema Identificado

As tabelas aparecem vazias na interface porque há um **desalinhamento entre os specs (JSON) e o schema do SQLite**. O `SQLiteAdapter.read_all()` tenta acessar campos que não existem nas tabelas, causando o erro:

```
ERROR:persistence.adapters.sqlite_adapter:Failed to read from [table]: No item with that key
```

## Tabelas Afetadas e Correções Necessárias

### 1. metodologias
**Campos faltantes no SQLite:**
- `versao` (text, não obrigatório)

**Ação:** Adicionar coluna `versao TEXT`

---

### 2. classificacao_amostras
**Problema de renomeação:**
- Spec usa: `classificacao` (referência a acreditador)
- SQLite tem: `nome` + `acreditador`

**Ação:** Alterar spec ou renomear colunas

---

### 3. fracionamento
**Problema de renomeação:**
- Spec usa: `entrada`, `data_hora`
- SQLite tem: `entrada_amostra`, `data_fracionamento`, `hora_fracionamento`

**Ação:** Sincronizar nomes de campos

---

### 4. laudo
**Campos faltantes no SQLite:**
- `observacoes` (textarea, não obrigatório)

**Campo extra no SQLite:**
- `status_tag` (não está no spec)

**Ação:** Adicionar `observacoes`, remover `status_tag` do spec ou adicionar no SQLite

---

### 5. precos_cliente
**Problema de renomeação:**
- Spec usa: `vigencia_inicio`, `vigencia_fim`
- SQLite tem: `data_inicio`, `data_fim`

**Ação:** Sincronizar nomes

---

### 6. tipos_amostras
**Problema de renomeação:**
- Spec usa: `tipo` (referência)
- SQLite tem: `nome`

**Ação:** Sincronizar nomes

---

### 7. analises_resultados
**Campos faltantes no SQLite:**
- `analise` (search, obrigatório)
- `analista` (search, obrigatório)
- `observacoes` (textarea, não obrigatório)

**Campo extra no SQLite:**
- `status_tag` (não está no spec)

**Ação:** Adicionar campos faltantes

---

## Causa Raiz

O problema ocorre na linha 227 do `src/persistence/adapters/sqlite_adapter.py`:

```python
value = row[field_name]  # Falha se field_name não existe na tabela
```

O código itera pelos campos do **spec** e tenta acessá-los na row retornada do SQLite. Se o campo não existir, lança `KeyError: "No item with that key"`.

## Soluções Possíveis

### Opção 1: Corrigir os Specs (Rápido)
Atualizar os specs para corresponder exatamente ao schema SQLite existente.

**Prós:**
- Rápido
- Não perde dados
- Sem migração

**Contras:**
- Specs podem estar corretos e SQLite desatualizado
- Não resolve problema estrutural

### Opção 2: Migrar o Schema SQLite (Recomendado)
Executar migração automática para alinhar SQLite com os specs.

**Prós:**
- Resolve definitivamente
- Usa sistema de migração do VibeCForms
- Mantém histórico

**Contras:**
- Mais complexo
- Requer backup

### Opção 3: Reconstruir Tabelas
Dropar e recriar as tabelas a partir dos specs, re-populando os dados.

**Prós:**
- Garante alinhamento total
- Limpa campos obsoletos

**Contras:**
- Perde dados (requer re-população)
- Mais demorado

## Recomendação

**Migrar o Schema SQLite** é a melhor opção porque:
1. O sistema já tem migração automática
2. Preserva os dados existentes
3. Mantém histórico de mudanças
4. Alinha com a arquitetura do VibeCForms

## Próximos Passos

1. ✅ Identificar todos os mismatches (CONCLUÍDO)
2. ⏳ Criar script de migração para ajustar schemas
3. ⏳ Executar migração com backup
4. ⏳ Validar que todas as tabelas exibem corretamente
5. ⏳ Documentar relacionamentos do workflow
