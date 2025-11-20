# Guia de Homologação - Sistema de Tags (FASE 5-7)

Este documento orienta a homologação completa do Sistema de Tags implementado no VibeCForms.

## Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Testes Automatizados](#testes-automatizados)
3. [Testes Funcionais Manuais](#testes-funcionais-manuais)
4. [Validação de Performance](#validação-de-performance)
5. [Checklist de Homologação](#checklist-de-homologação)
6. [Critérios de Aceite](#critérios-de-aceite)

---

## Pré-requisitos

### Ambiente Configurado
```bash
# Verificar que o ambiente está atualizado
uv sync

# Verificar que a aplicação inicia sem erros
uv run hatch run dev
```

A aplicação deve iniciar em http://0.0.0.0:5000

### Configuração Necessária
- SQLite configurado em `src/config/persistence.json`
- Tabela `tags` criada automaticamente no banco
- Pelo menos um formulário configurado (ex: "contatos")

---

## Testes Automatizados

### 1. Testes E2E do Sistema de Tags

Execute a suíte completa de testes E2E:

```bash
uv run pytest tests/test_tags_e2e.py -v
```

**Resultado esperado:**
```
============================== 15 passed ==============================
```

**Cobertura dos testes:**
- ✅ Adicionar tags a objetos
- ✅ Validação de nomes de tags (apenas lowercase, números, underscore)
- ✅ Remover tags
- ✅ Listar tags ativas
- ✅ Obter apenas nomes de tags
- ✅ Transição entre estados (tags)
- ✅ Verificar se objeto tem alguma tag específica
- ✅ Verificar se objeto tem todas as tags
- ✅ Remover todas as tags de um objeto
- ✅ Buscar objetos por tag
- ✅ Formato de UUID (27 caracteres Crockford Base32)
- ✅ Persistência de UUID após operações de tag
- ✅ Unicidade de UUIDs
- ✅ Histórico de tags (ativas vs removidas)
- ✅ Padrão Singleton do TagService

### 2. Testes de Integração Existentes

Execute todos os testes do projeto:

```bash
uv run hatch run test
```

**Resultado esperado:**
```
============================== 16 passed ==============================
```

Todos os 16 testes originais devem continuar passando (zero regressão).

---

## Testes Funcionais Manuais

### 3. Teste Manual - Operações Básicas de Tags

#### 3.1 Criar Registros de Teste

1. Acesse http://localhost:5000/contatos
2. Crie 5 registros de teste:
   - Nome: "Lead 1", Email: "lead1@example.com"
   - Nome: "Lead 2", Email: "lead2@example.com"
   - Nome: "Cliente 1", Email: "cliente1@example.com"
   - Nome: "Cliente 2", Email: "cliente2@example.com"
   - Nome: "Inativo 1", Email: "inativo1@example.com"

#### 3.2 Adicionar Tags via Console Python

```bash
# Abrir console Python no ambiente virtual
uv run python
```

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

from services.tag_service import get_tag_service
from persistence.factory import RepositoryFactory

# Obter IDs dos registros
repo = RepositoryFactory.get_repository("contatos")
from specs_loader import load_form_spec
spec = load_form_spec("contatos")
records = repo.read_all("contatos", spec)

# Mostrar IDs
for i, record in enumerate(records):
    print(f"{i}: {record['nome']} - ID: {record['_record_id']}")

# Guardar IDs (ajustar conforme saída)
lead1_id = records[0]['_record_id']
lead2_id = records[1]['_record_id']
cliente1_id = records[2]['_record_id']
cliente2_id = records[3]['_record_id']
inativo1_id = records[4]['_record_id']

# Obter tag service
tag_service = get_tag_service()

# Adicionar tags
tag_service.add_tag("contatos", lead1_id, "lead", "sistema")
tag_service.add_tag("contatos", lead2_id, "lead", "sistema")
tag_service.add_tag("contatos", cliente1_id, "cliente", "vendedor1")
tag_service.add_tag("contatos", cliente2_id, "cliente", "vendedor2")
tag_service.add_tag("contatos", inativo1_id, "inativo", "sistema")

# Adicionar tag de prioridade a um lead
tag_service.add_tag("contatos", lead1_id, "prioridade", "gerente")

print("✅ Tags adicionadas com sucesso!")
```

#### 3.3 Validar Tags

Continue no console Python:

```python
# Verificar tags de um registro
tags_lead1 = tag_service.get_tags("contatos", lead1_id, active_only=True)
print(f"Tags do Lead 1: {[t['tag'] for t in tags_lead1]}")
# Esperado: ['lead', 'prioridade']

# Verificar se tem tag específica
print(f"Lead 1 é lead? {tag_service.has_tag('contatos', lead1_id, 'lead')}")
# Esperado: True

print(f"Lead 1 é cliente? {tag_service.has_tag('contatos', lead1_id, 'cliente')}")
# Esperado: False

# Buscar todos os leads
leads = tag_service.get_objects_with_tag("contatos", "lead")
print(f"Total de leads: {len(leads)}")
# Esperado: 2

# Buscar todos os clientes
clientes = tag_service.get_objects_with_tag("contatos", "cliente")
print(f"Total de clientes: {len(clientes)}")
# Esperado: 2
```

#### 3.4 Testar Transições de Estado

Continue no console Python:

```python
# Promover lead para cliente
success = tag_service.transition(
    "contatos", lead1_id,
    from_tag="lead",
    to_tag="cliente",
    actor="vendedor1",
    metadata={"motivo": "Fechou contrato"}
)
print(f"Transição bem-sucedida? {success}")
# Esperado: True

# Verificar nova tag
print(f"Lead 1 ainda é lead? {tag_service.has_tag('contatos', lead1_id, 'lead')}")
# Esperado: False

print(f"Lead 1 agora é cliente? {tag_service.has_tag('contatos', lead1_id, 'cliente')}")
# Esperado: True

# Tag de prioridade deve permanecer
print(f"Lead 1 ainda tem prioridade? {tag_service.has_tag('contatos', lead1_id, 'prioridade')}")
# Esperado: True
```

#### 3.5 Testar Remoção de Tags

```python
# Remover tag de prioridade
success = tag_service.remove_tag("contatos", lead1_id, "prioridade", "gerente")
print(f"Remoção bem-sucedida? {success}")
# Esperado: True

# Verificar remoção
print(f"Lead 1 ainda tem prioridade? {tag_service.has_tag('contatos', lead1_id, 'prioridade')}")
# Esperado: False

# Ver histórico completo (incluindo tags removidas)
todas_tags = tag_service.get_tags("contatos", lead1_id, active_only=False)
print(f"Total de tags (incluindo removidas): {len(todas_tags)}")
# Esperado: >= 3 (lead, cliente, prioridade)
```

#### 3.6 Validar Nomes de Tags

```python
# Tentar adicionar tag com nome inválido
resultado = tag_service.add_tag("contatos", cliente1_id, "Tag Inválida", "teste")
print(f"Tag com espaço aceita? {resultado}")
# Esperado: False

resultado = tag_service.add_tag("contatos", cliente1_id, "tag-invalida", "teste")
print(f"Tag com hífen aceita? {resultado}")
# Esperado: False

resultado = tag_service.add_tag("contatos", cliente1_id, "TAG_MAIUSCULA", "teste")
print(f"Tag com maiúsculas aceita? {resultado}")
# Esperado: False

# Tag válida deve funcionar
resultado = tag_service.add_tag("contatos", cliente1_id, "tag_valida_123", "teste")
print(f"Tag válida aceita? {resultado}")
# Esperado: True
```

---

## Validação de Performance

### 4. Executar Benchmarks

Execute a suíte de benchmarks de performance:

```bash
uv run pytest tests/benchmark_performance.py -v -s
```

**Resultados esperados (referência):**

#### Bulk Create - TXT Backend
- 10 registros: ~50,000+ records/sec
- 100 registros: ~100,000+ records/sec
- 1000 registros: ~110,000+ records/sec

#### Bulk Create - SQLite Backend
- 10 registros: ~1,000+ records/sec
- 100 registros: ~10,000+ records/sec
- 1000 registros: ~50,000+ records/sec

#### Migração TXT → SQLite
- 100 registros: <0.025s (total)
- 500 registros: <0.030s (total)

#### Operações de Tags
- Adicionar tag: <1ms
- Verificar tag: <0.2ms
- Buscar objetos por tag: <0.2ms
- Remover tag: <1ms

#### Leitura (SQLite)
- 100 registros: ~170,000+ records/sec
- 1000 registros: ~460,000+ records/sec

**Nota:** Os valores reais podem variar dependendo do hardware, mas devem estar na mesma ordem de grandeza.

---

## Checklist de Homologação

### ✅ Funcionalidades Implementadas

- [ ] **TagService Singleton**
  - [ ] `get_tag_service()` retorna sempre a mesma instância

- [ ] **Operações Básicas de Tags**
  - [ ] `add_tag(form_path, object_id, tag, actor)` - adiciona tag
  - [ ] `remove_tag(form_path, object_id, tag, actor)` - remove tag
  - [ ] `has_tag(form_path, object_id, tag)` - verifica tag
  - [ ] `get_tags(form_path, object_id, active_only=True)` - lista tags
  - [ ] `get_tag_names(form_path, object_id)` - lista só nomes

- [ ] **Operações Avançadas**
  - [ ] `transition(form_path, object_id, from_tag, to_tag, actor)` - transição de estado
  - [ ] `has_any_tag(form_path, object_id, tags)` - verifica se tem alguma das tags
  - [ ] `has_all_tags(form_path, object_id, tags)` - verifica se tem todas as tags
  - [ ] `remove_all_tags(form_path, object_id, actor)` - remove todas as tags
  - [ ] `get_objects_with_tag(form_path, tag)` - busca objetos por tag

- [ ] **Validação**
  - [ ] Nomes de tags aceitam apenas: lowercase, números, underscore
  - [ ] Nomes de tags rejeitam: maiúsculas, espaços, caracteres especiais

- [ ] **Persistência**
  - [ ] Tags persistem no banco SQLite (tabela `tags`)
  - [ ] UUIDs são gerados automaticamente (27 caracteres)
  - [ ] UUIDs permanecem consistentes após operações
  - [ ] Histórico de tags é mantido (tags removidas ficam marcadas)

- [ ] **Performance**
  - [ ] Bulk create otimizado com `executemany()`
  - [ ] Operações de tag em <1ms
  - [ ] Migrações concluem em tempo aceitável

- [ ] **Testes**
  - [ ] 15 testes E2E passando
  - [ ] 16 testes de integração passando (zero regressão)
  - [ ] 11 benchmarks executam com sucesso

### ✅ Arquivos Criados/Modificados

**Novos Arquivos:**
- [ ] `src/services/tag_service.py` - Serviço de tags
- [ ] `tests/test_tags_e2e.py` - Testes E2E
- [ ] `tests/benchmark_performance.py` - Benchmarks
- [ ] `docs/homologacao_tags.md` - Este documento

**Modificados (Otimizações):**
- [ ] `src/persistence/schema_history.py` - Adicionado `flush()` + `fsync()` + verificação
- [ ] `src/persistence/adapters/sqlite_adapter.py` - Bulk create com `executemany()`
- [ ] `src/persistence/migration_manager.py` - Logs detalhados com emojis e timing

---

## Critérios de Aceite

### ✅ Critério 1: Testes Automatizados
**Status:** DEVE passar todos os testes sem erros

```bash
# E2E Tags
uv run pytest tests/test_tags_e2e.py -v
# Esperado: 15 passed

# Integração
uv run hatch run test
# Esperado: 16 passed

# Benchmarks
uv run pytest tests/benchmark_performance.py -v -s
# Esperado: 11 passed
```

### ✅ Critério 2: Funcionalidade Manual
**Status:** DEVE executar fluxo completo sem erros

1. Criar registros
2. Adicionar tags
3. Verificar tags
4. Buscar por tags
5. Fazer transições
6. Remover tags
7. Validar regras de nomes

### ✅ Critério 3: Performance
**Status:** DEVE atender métricas mínimas

- Operações de tag: <1ms
- Bulk create 1000 registros: <0.1s (SQLite)
- Migração 500 registros: <0.05s
- Zero degradação em testes existentes

### ✅ Critério 4: Persistência
**Status:** DEVE manter integridade dos dados

- UUIDs únicos e persistentes
- Tags persistem entre reinícios
- Histórico completo de tags
- Zero perda de dados em migrações

### ✅ Critério 5: Zero Regressão
**Status:** DEVE manter funcionalidade existente

- Todos os 16 testes originais passando
- Funcionalidades de formulários intactas
- Performance não degradada

---

## Processo de Homologação Passo a Passo

### Dia 1: Testes Automatizados (30 minutos)

1. **Clone ambiente limpo (opcional)**
   ```bash
   git clone <repo> vibecforms-homolog
   cd vibecforms-homolog
   uv sync
   ```

2. **Execute testes E2E**
   ```bash
   uv run pytest tests/test_tags_e2e.py -v
   ```
   ✅ Verificar: 15 passed

3. **Execute testes de integração**
   ```bash
   uv run hatch run test
   ```
   ✅ Verificar: 16 passed

4. **Execute benchmarks**
   ```bash
   uv run pytest tests/benchmark_performance.py -v -s
   ```
   ✅ Verificar: 11 passed
   ✅ Anotar métricas de performance

### Dia 2: Testes Funcionais (45 minutos)

1. **Iniciar aplicação**
   ```bash
   uv run hatch run dev
   ```

2. **Criar registros de teste** (veja seção 3.1)

3. **Testar operações básicas** (veja seção 3.2-3.3)

4. **Testar transições** (veja seção 3.4)

5. **Testar remoção** (veja seção 3.5)

6. **Testar validação** (veja seção 3.6)

### Dia 3: Validação Final (15 minutos)

1. **Reiniciar aplicação**
   ```bash
   # Parar e reiniciar
   uv run hatch run dev
   ```

2. **Verificar persistência**
   - Tags criadas ontem devem estar presentes
   - UUIDs devem ser os mesmos

3. **Executar teste de carga (opcional)**
   - Criar 1000+ registros
   - Adicionar tags em massa
   - Verificar performance

4. **Preencher checklist**
   - Marcar todos os itens validados
   - Anotar quaisquer observações

---

## Troubleshooting

### Problema: Testes E2E falhando

**Sintoma:** `AssertionError` em `test_get_objects_with_tag`

**Causa:** Tags de execuções anteriores no banco

**Solução:**
```bash
# Limpar banco de testes
rm -f /tmp/pytest-*/test.db
# Ou verificar que testes usam nomes únicos
```

### Problema: Performance abaixo do esperado

**Sintoma:** Benchmarks lentos

**Causa possível:** I/O de disco lento, muitos processos rodando

**Solução:**
- Fechar outros programas
- Executar em SSD se possível
- Verificar se `executemany()` está sendo usado (logs devem mostrar)

### Problema: UUIDs não persistem

**Sintoma:** UUIDs mudam após operações

**Causa:** Bug na camada de persistência

**Solução:**
```python
# Verificar que _record_id está sendo preservado
records = repo.read_all("form", spec)
print(records[0].get('_record_id'))  # Deve existir
```

---

## Resultado Final

Após completar todos os passos:

**✅ Sistema APROVADO se:**
- Todos os testes automatizados passam
- Testes funcionais executam sem erros
- Performance atende critérios mínimos
- Zero regressão identificada
- Dados persistem corretamente

**❌ Sistema REPROVADO se:**
- Qualquer teste automatizado falha
- Funcionalidades básicas não funcionam
- Performance significativamente degradada
- Regressão detectada em funcionalidades existentes
- Perda de dados ou corrupção detectada

---

## Contato e Suporte

Para dúvidas ou problemas durante a homologação:
- Verifique logs detalhados com emojis nos arquivos de log
- Consulte `CLAUDE.md` para documentação técnica
- Execute testes com `-v` para output detalhado
- Use `--tb=long` em pytest para traces completos

---

**Última atualização:** 2025-01-XX (FASE 7 completa)
**Versão:** 3.0.0 (Tags-as-State)
