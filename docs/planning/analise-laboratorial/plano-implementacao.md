# Plano de Implementação: Sistema LIMS - Análises Laboratoriais
## VibeCForms - Controle de Qualidade de Água e Alimentos

**Data:** 2025-12-26
**Versão:** 2.0 (Refatoração Completa)
**Projeto:** /home/rodrigo/VibeCForms
**Business Case:** examples/analise-laboratorial/

---

## Sumário Executivo

Sistema LIMS (Laboratory Information Management System) para laboratórios de controle de qualidade de água e alimentos, implementado com o framework VibeCForms.

### Requisitos Definidos

| Aspecto | Decisão |
|---------|---------|
| Rastreabilidade | **Completa (ISO 17025)** |
| CQ Interno | **Básico** (campo opcional) |
| Aprovação | **2 níveis** (Analista → RT) |
| Documentos | **Laudo único** |
| Coleta | **Ambos** (recebe e coleta externa) |
| Equipamentos | **Fora do escopo** |
| Usuários | **Sem autenticação** (cadastro simples) |
| Precificação | **Tabela por cliente** |
| Numeração Laudo | **Por acreditador** (MAPA-001/25) |
| Hierarquia Amostras | **3 níveis** |

### Arquitetura Final

- **17 entidades** principais
- **4 Kanban boards** para workflow
- **Persistência SQLite** com UUIDs Crockford Base32
- **Cadeia de custódia** ISO 17025 completa

---

## Modelo de Dados

### Diagrama de Entidades

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTIDADES BASE (4)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    CLIENTES     │    │  FUNCIONARIOS   │    │  ACREDITADORES  │         │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤         │
│  │ nome            │    │ nome            │    │ nome            │         │
│  │ cpf_cnpj        │    │ funcao          │    │ sigla           │         │
│  │ codigo_sif      │    │ crq             │    │ tipo_certificado│         │
│  │ codigo_ima      │    │ ativo           │    └─────────────────┘         │
│  │ email           │    └─────────────────┘                                │
│  │ telefone        │                           ┌─────────────────┐         │
│  │ endereco        │                           │  METODOLOGIAS   │         │
│  │ cidade          │                           ├─────────────────┤         │
│  │ uf              │                           │ nome            │         │
│  │ cep             │                           │ bibliografia    │         │
│  └─────────────────┘                           │ referencia      │         │
│                                                │ versao          │         │
│                                                └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      HIERARQUIA DE AMOSTRAS (3 níveis)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────┐                                                  │
│  │ CLASSIFICACAO_AMOSTRAS│  Nível 1: Por Acreditador                       │
│  ├───────────────────────┤  Ex: "Produtos de Origem Animal" (MAPA)         │
│  │ acreditador (FK)      │──────┐                                          │
│  │ classificacao         │      │                                          │
│  └───────────────────────┘      │                                          │
│            │                    │                                          │
│            ▼                    │                                          │
│  ┌───────────────────────┐      │                                          │
│  │    TIPOS_AMOSTRAS     │  Nível 2: Agrupamento                           │
│  ├───────────────────────┤  Ex: "Embutidos", "Lácteos", "Água Potável"     │
│  │ classificacao (FK)    │──────┘                                          │
│  │ tipo                  │                                                  │
│  │ temperatura_padrao    │                                                  │
│  └───────────────────────┘                                                  │
│            │                                                                │
│            ▼                                                                │
│  ┌───────────────────────┐                                                  │
│  │  AMOSTRAS_ESPECIFICAS │  Nível 3: Detalhamento                          │
│  ├───────────────────────┤  Ex: "Presunto", "Salame", "Linguiça Calabresa" │
│  │ tipo_amostra (FK)     │                                                  │
│  │ nome                  │                                                  │
│  │ codigo                │                                                  │
│  └───────────────────────┘                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CATÁLOGO DE ANÁLISES (4)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐      ┌─────────────────────┐                      │
│  │      ANALISES       │      │ RESULTADOS_PARCIAIS │                      │
│  ├─────────────────────┤      ├─────────────────────┤                      │
│  │ nome_oficial        │◄─────│ analise (FK)        │                      │
│  │ tipo                │      │ nome_parcial        │                      │
│  │ tem_parciais        │      │ formula             │                      │
│  │ gera_complementar   │      │ ordem               │                      │
│  │ analise_complem(FK) │──┐   └─────────────────────┘                      │
│  └─────────────────────┘  │                                                │
│            │              │   (autorelacionamento)                         │
│            └──────────────┘                                                │
│                                                                             │
│  ┌─────────────────────┐      ┌─────────────────────┐                      │
│  │   MATRIZ_ANALISES   │      │   PRECOS_CLIENTE    │                      │
│  ├─────────────────────┤      ├─────────────────────┤                      │
│  │ analise (FK)        │◄─────│ matriz_analise (FK) │                      │
│  │ tipo_amostra (FK)   │      │ cliente (FK)        │                      │
│  │ metodologia (FK)    │      │ valor_especial      │                      │
│  │ padrao_referencia   │      │ desconto_percentual │                      │
│  │ valor_base          │      │ vigencia_inicio     │                      │
│  └─────────────────────┘      │ vigencia_fim        │                      │
│                               └─────────────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO OPERACIONAL - CADEIA DE CUSTÓDIA (6)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐                                                    │
│  │    ORCAMENTO_OS     │  Orçamento → Ordem de Serviço                     │
│  ├─────────────────────┤                                                    │
│  │ cliente (FK)        │                                                    │
│  │ acreditador (FK)    │                                                    │
│  │ data_inclusao       │                                                    │
│  │ partes              │                                                    │
│  │ qtd_amostras        │                                                    │
│  │ urgencia            │  (+50% se urgente)                                │
│  │ valor_coleta        │                                                    │
│  │ taxa_administrativa │                                                    │
│  │ subtotal            │                                                    │
│  │ valor_total         │                                                    │
│  │ aprovado            │                                                    │
│  │ data_aprovacao      │                                                    │
│  └─────────┬───────────┘                                                    │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────┐                                                    │
│  │       COLETA        │  (Opcional - quando lab faz coleta externa)       │
│  ├─────────────────────┤                                                    │
│  │ orcamento_os (FK)   │                                                    │
│  │ data_hora           │                                                    │
│  │ local               │                                                    │
│  │ coletor (FK)        │  → Funcionário                                    │
│  │ condicoes           │                                                    │
│  │ numero_lacre        │                                                    │
│  │ observacoes         │                                                    │
│  └─────────┬───────────┘                                                    │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────┐                                                    │
│  │   ENTRADA_AMOSTRA   │  Recepção no laboratório                          │
│  ├─────────────────────┤                                                    │
│  │ orcamento_os (FK)   │                                                    │
│  │ coleta (FK)         │  (opcional)                                       │
│  │ data_entrada        │                                                    │
│  │ recebedor (FK)      │  → Funcionário                                    │
│  │ amostra_especif(FK) │  → Amostra específica                             │
│  │ descricao           │                                                    │
│  │ quantidade          │                                                    │
│  │ temperatura         │                                                    │
│  │ lacre_ok            │                                                    │
│  │ conferido_ok        │                                                    │
│  │ anomalias           │                                                    │
│  └─────────┬───────────┘                                                    │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────┐                                                    │
│  │    FRACIONAMENTO    │  Divisão em porções para análise                  │
│  ├─────────────────────┤                                                    │
│  │ entrada (FK)        │                                                    │
│  │ numero_porcao       │                                                    │
│  │ tipo_analise        │  (Físico-Química / Microbiológica)                │
│  │ responsavel (FK)    │  → Funcionário                                    │
│  │ data_hora           │                                                    │
│  └─────────┬───────────┘                                                    │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────┐                                                    │
│  │ ANALISES_RESULTADOS │  Execução e resultado da análise                  │
│  ├─────────────────────┤                                                    │
│  │ fracionamento (FK)  │                                                    │
│  │ analise (FK)        │                                                    │
│  │ matriz_analise (FK) │                                                    │
│  │ analista (FK)       │  → Funcionário que executou                       │
│  │ inicio_analise      │                                                    │
│  │ termino_analise     │                                                    │
│  │ resultado_previo    │                                                    │
│  │ resultado_final     │                                                    │
│  │ conformidade        │  (Conforme / Não Conforme)                        │
│  │ cqi_ok              │  (Controle qualidade básico)                      │
│  │ observacoes         │                                                    │
│  └─────────┬───────────┘                                                    │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────┐                                                    │
│  │        LAUDO        │  Documento final                                  │
│  ├─────────────────────┤                                                    │
│  │ orcamento_os (FK)   │                                                    │
│  │ numero              │  Ex: MAPA-001/2025, IMA-002/2025                  │
│  │ acreditador (FK)    │  (para numeração separada)                        │
│  │ data_emissao        │                                                    │
│  │ rt (FK)             │  → Responsável Técnico                            │
│  │ parecer             │  (Conforme / Não Conforme / Parcial)              │
│  │ observacoes         │                                                    │
│  └─────────────────────┘                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretórios

```
examples/analise-laboratorial/
├── specs/
│   ├── _folder.json                    # Config: "Laboratório QA" icon="fa-flask"
│   │
│   ├── # ENTIDADES BASE (4)
│   ├── clientes.json
│   ├── funcionarios.json
│   ├── acreditadores.json
│   ├── metodologias.json
│   │
│   ├── # HIERARQUIA DE AMOSTRAS (3)
│   ├── classificacao_amostras.json
│   ├── tipos_amostras.json
│   ├── amostras_especificas.json
│   │
│   ├── # CATÁLOGO DE ANÁLISES (4)
│   ├── analises.json
│   ├── resultados_parciais.json
│   ├── matriz_analises.json
│   ├── precos_cliente.json
│   │
│   └── # FLUXO OPERACIONAL (6)
│       ├── orcamento_os.json
│       ├── coleta.json
│       ├── entrada_amostra.json
│       ├── fracionamento.json
│       ├── analises_resultados.json
│       └── laudo.json
│
├── config/
│   ├── persistence.json                # SQLite para todas entidades
│   ├── schema_history.json             # Histórico de schemas
│   └── kanban_boards.json              # 4 boards de workflow
│
├── data/
│   └── sqlite/
│       └── vibecforms.db               # Banco SQLite
│
├── backups/
│   └── migrations/
│
└── templates/                          # Templates customizados (opcional)
```

---

## Especificações das Entidades

### 1. CLIENTES
```json
{
  "title": "Clientes",
  "icon": "fa-building",
  "fields": [
    {"name": "nome", "label": "Nome / Razão Social", "type": "text", "required": true},
    {"name": "cpf_cnpj", "label": "CPF / CNPJ", "type": "text", "required": true},
    {"name": "codigo_sif", "label": "Código SIF", "type": "text", "required": false},
    {"name": "codigo_ima", "label": "Código IMA", "type": "text", "required": false},
    {"name": "email", "label": "E-mail", "type": "email", "required": true},
    {"name": "telefone", "label": "Telefone", "type": "tel", "required": true},
    {"name": "endereco", "label": "Endereço", "type": "text", "required": false},
    {"name": "cidade", "label": "Cidade", "type": "text", "required": false},
    {"name": "uf", "label": "UF", "type": "text", "required": false},
    {"name": "cep", "label": "CEP", "type": "text", "required": false}
  ]
}
```

### 2. FUNCIONARIOS
```json
{
  "title": "Funcionários",
  "icon": "fa-user-tie",
  "fields": [
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "funcao", "label": "Função", "type": "select", "required": true,
      "options": [
        {"value": "analista", "label": "Analista"},
        {"value": "supervisor", "label": "Supervisor"},
        {"value": "rt", "label": "Responsável Técnico"},
        {"value": "coletor", "label": "Coletor"},
        {"value": "recepcao", "label": "Recepção"},
        {"value": "administrativo", "label": "Administrativo"}
      ]
    },
    {"name": "crq", "label": "CRQ (se aplicável)", "type": "text", "required": false},
    {"name": "ativo", "label": "Ativo", "type": "checkbox", "required": false}
  ]
}
```

### 3. ACREDITADORES
```json
{
  "title": "Acreditadores",
  "icon": "fa-certificate",
  "fields": [
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "sigla", "label": "Sigla", "type": "text", "required": true},
    {"name": "tipo_certificado", "label": "Tipo de Certificado", "type": "select", "required": true,
      "options": [
        {"value": "oficial", "label": "Certificado Oficial"},
        {"value": "laudo", "label": "Laudo Padrão"}
      ]
    }
  ]
}
```

### 4. METODOLOGIAS
```json
{
  "title": "Metodologias",
  "icon": "fa-book",
  "fields": [
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "bibliografia", "label": "Bibliografia", "type": "text", "required": true},
    {"name": "referencia", "label": "Referência", "type": "text", "required": true},
    {"name": "versao", "label": "Versão", "type": "text", "required": false}
  ]
}
```

### 5. CLASSIFICACAO_AMOSTRAS
```json
{
  "title": "Classificação de Amostras",
  "icon": "fa-layer-group",
  "fields": [
    {"name": "acreditador", "label": "Acreditador", "type": "search", "datasource": "acreditadores", "required": true},
    {"name": "classificacao", "label": "Classificação", "type": "text", "required": true}
  ]
}
```

### 6. TIPOS_AMOSTRAS
```json
{
  "title": "Tipos de Amostras",
  "icon": "fa-vials",
  "fields": [
    {"name": "classificacao", "label": "Classificação", "type": "search", "datasource": "classificacao_amostras", "required": true},
    {"name": "tipo", "label": "Tipo", "type": "text", "required": true},
    {"name": "temperatura_padrao", "label": "Temperatura Padrão (°C)", "type": "number", "required": false}
  ]
}
```

### 7. AMOSTRAS_ESPECIFICAS
```json
{
  "title": "Amostras Específicas",
  "icon": "fa-flask",
  "fields": [
    {"name": "tipo_amostra", "label": "Tipo de Amostra", "type": "search", "datasource": "tipos_amostras", "required": true},
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "codigo", "label": "Código", "type": "text", "required": false}
  ]
}
```

### 8. ANALISES
```json
{
  "title": "Análises",
  "icon": "fa-microscope",
  "fields": [
    {"name": "nome_oficial", "label": "Nome Oficial", "type": "text", "required": true},
    {"name": "tipo", "label": "Tipo", "type": "select", "required": true,
      "options": [
        {"value": "fisico_quimica", "label": "Físico-Química"},
        {"value": "microbiologica", "label": "Microbiológica"}
      ]
    },
    {"name": "tem_parciais", "label": "Tem Resultados Parciais", "type": "checkbox", "required": false},
    {"name": "gera_complementar", "label": "Gera Análise Complementar", "type": "checkbox", "required": false},
    {"name": "analise_complementar", "label": "Análise Complementar", "type": "search", "datasource": "analises", "required": false}
  ]
}
```

### 9. RESULTADOS_PARCIAIS
```json
{
  "title": "Resultados Parciais",
  "icon": "fa-list-ol",
  "fields": [
    {"name": "analise", "label": "Análise", "type": "search", "datasource": "analises", "required": true},
    {"name": "nome_parcial", "label": "Nome do Resultado Parcial", "type": "text", "required": true},
    {"name": "formula", "label": "Fórmula/Cálculo", "type": "textarea", "required": false},
    {"name": "ordem", "label": "Ordem", "type": "number", "required": true}
  ]
}
```

### 10. MATRIZ_ANALISES
```json
{
  "title": "Matriz de Análises",
  "icon": "fa-table",
  "fields": [
    {"name": "analise", "label": "Análise", "type": "search", "datasource": "analises", "required": true},
    {"name": "tipo_amostra", "label": "Tipo de Amostra", "type": "search", "datasource": "tipos_amostras", "required": true},
    {"name": "metodologia", "label": "Metodologia", "type": "search", "datasource": "metodologias", "required": true},
    {"name": "padrao_referencia", "label": "Padrão de Referência", "type": "text", "required": true},
    {"name": "valor_base", "label": "Valor Base (R$)", "type": "number", "required": true}
  ]
}
```

### 11. PRECOS_CLIENTE
```json
{
  "title": "Preços por Cliente",
  "icon": "fa-tags",
  "fields": [
    {"name": "cliente", "label": "Cliente", "type": "search", "datasource": "clientes", "required": true},
    {"name": "matriz_analise", "label": "Matriz de Análise", "type": "search", "datasource": "matriz_analises", "required": true},
    {"name": "valor_especial", "label": "Valor Especial (R$)", "type": "number", "required": false},
    {"name": "desconto_percentual", "label": "Desconto (%)", "type": "number", "required": false},
    {"name": "vigencia_inicio", "label": "Vigência Início", "type": "date", "required": true},
    {"name": "vigencia_fim", "label": "Vigência Fim", "type": "date", "required": false}
  ]
}
```

### 12. ORCAMENTO_OS
```json
{
  "title": "Orçamento / OS",
  "icon": "fa-file-invoice-dollar",
  "fields": [
    {"name": "cliente", "label": "Cliente", "type": "search", "datasource": "clientes", "required": true},
    {"name": "acreditador", "label": "Acreditador", "type": "search", "datasource": "acreditadores", "required": true},
    {"name": "data_inclusao", "label": "Data de Inclusão", "type": "date", "required": true},
    {"name": "partes", "label": "Partes Interessadas", "type": "textarea", "required": false},
    {"name": "qtd_amostras", "label": "Quantidade de Amostras", "type": "number", "required": true},
    {"name": "urgencia", "label": "Urgência (+50%)", "type": "checkbox", "required": false},
    {"name": "valor_coleta", "label": "Valor Coleta (R$)", "type": "number", "required": false},
    {"name": "taxa_administrativa", "label": "Taxa Administrativa (R$)", "type": "number", "required": false},
    {"name": "subtotal", "label": "Subtotal (R$)", "type": "number", "required": false},
    {"name": "valor_total", "label": "Valor Total (R$)", "type": "number", "required": false},
    {"name": "aprovado", "label": "Aprovado", "type": "checkbox", "required": false},
    {"name": "data_aprovacao", "label": "Data de Aprovação", "type": "date", "required": false}
  ]
}
```

### 13. COLETA
```json
{
  "title": "Coleta",
  "icon": "fa-truck",
  "fields": [
    {"name": "orcamento_os", "label": "Orçamento/OS", "type": "search", "datasource": "orcamento_os", "required": true},
    {"name": "data_hora", "label": "Data/Hora", "type": "datetime-local", "required": true},
    {"name": "local", "label": "Local de Coleta", "type": "text", "required": true},
    {"name": "coletor", "label": "Coletor", "type": "search", "datasource": "funcionarios", "required": true},
    {"name": "condicoes", "label": "Condições da Coleta", "type": "textarea", "required": false},
    {"name": "numero_lacre", "label": "Número do Lacre", "type": "text", "required": false},
    {"name": "observacoes", "label": "Observações", "type": "textarea", "required": false}
  ]
}
```

### 14. ENTRADA_AMOSTRA
```json
{
  "title": "Entrada de Amostra",
  "icon": "fa-sign-in-alt",
  "fields": [
    {"name": "orcamento_os", "label": "Orçamento/OS", "type": "search", "datasource": "orcamento_os", "required": true},
    {"name": "coleta", "label": "Coleta (se houver)", "type": "search", "datasource": "coleta", "required": false},
    {"name": "data_entrada", "label": "Data de Entrada", "type": "datetime-local", "required": true},
    {"name": "recebedor", "label": "Recebedor", "type": "search", "datasource": "funcionarios", "required": true},
    {"name": "amostra_especifica", "label": "Amostra", "type": "search", "datasource": "amostras_especificas", "required": true},
    {"name": "descricao", "label": "Descrição", "type": "text", "required": false},
    {"name": "quantidade", "label": "Quantidade", "type": "number", "required": true},
    {"name": "temperatura", "label": "Temperatura (°C)", "type": "number", "required": true},
    {"name": "lacre_ok", "label": "Lacre OK", "type": "checkbox", "required": false},
    {"name": "conferido_ok", "label": "Conferido OK", "type": "checkbox", "required": false},
    {"name": "anomalias", "label": "Anomalias", "type": "textarea", "required": false}
  ]
}
```

### 15. FRACIONAMENTO
```json
{
  "title": "Fracionamento",
  "icon": "fa-cut",
  "fields": [
    {"name": "entrada", "label": "Entrada de Amostra", "type": "search", "datasource": "entrada_amostra", "required": true},
    {"name": "numero_porcao", "label": "Número da Porção", "type": "number", "required": true},
    {"name": "tipo_analise", "label": "Tipo de Análise", "type": "select", "required": true,
      "options": [
        {"value": "fisico_quimica", "label": "Físico-Química"},
        {"value": "microbiologica", "label": "Microbiológica"}
      ]
    },
    {"name": "responsavel", "label": "Responsável", "type": "search", "datasource": "funcionarios", "required": true},
    {"name": "data_hora", "label": "Data/Hora", "type": "datetime-local", "required": true}
  ]
}
```

### 16. ANALISES_RESULTADOS
```json
{
  "title": "Análises e Resultados",
  "icon": "fa-clipboard-check",
  "fields": [
    {"name": "fracionamento", "label": "Fracionamento", "type": "search", "datasource": "fracionamento", "required": true},
    {"name": "analise", "label": "Análise", "type": "search", "datasource": "analises", "required": true},
    {"name": "matriz_analise", "label": "Matriz de Análise", "type": "search", "datasource": "matriz_analises", "required": true},
    {"name": "analista", "label": "Analista", "type": "search", "datasource": "funcionarios", "required": true},
    {"name": "inicio_analise", "label": "Início da Análise", "type": "datetime-local", "required": true},
    {"name": "termino_analise", "label": "Término da Análise", "type": "datetime-local", "required": false},
    {"name": "resultado_previo", "label": "Resultado Prévio", "type": "text", "required": false},
    {"name": "resultado_final", "label": "Resultado Final", "type": "text", "required": false},
    {"name": "conformidade", "label": "Conformidade", "type": "select", "required": false,
      "options": [
        {"value": "conforme", "label": "Conforme"},
        {"value": "nao_conforme", "label": "Não Conforme"},
        {"value": "inconclusivo", "label": "Inconclusivo"}
      ]
    },
    {"name": "cqi_ok", "label": "CQI OK", "type": "checkbox", "required": false},
    {"name": "observacoes", "label": "Observações", "type": "textarea", "required": false}
  ]
}
```

### 17. LAUDO
```json
{
  "title": "Laudos",
  "icon": "fa-file-alt",
  "fields": [
    {"name": "orcamento_os", "label": "Orçamento/OS", "type": "search", "datasource": "orcamento_os", "required": true},
    {"name": "numero", "label": "Número do Laudo", "type": "text", "required": true},
    {"name": "acreditador", "label": "Acreditador", "type": "search", "datasource": "acreditadores", "required": true},
    {"name": "data_emissao", "label": "Data de Emissão", "type": "date", "required": true},
    {"name": "rt", "label": "Responsável Técnico", "type": "search", "datasource": "funcionarios", "required": true},
    {"name": "parecer", "label": "Parecer", "type": "select", "required": true,
      "options": [
        {"value": "conforme", "label": "Conforme"},
        {"value": "nao_conforme", "label": "Não Conforme"},
        {"value": "parcial", "label": "Parcialmente Conforme"}
      ]
    },
    {"name": "observacoes", "label": "Observações", "type": "textarea", "required": false}
  ]
}
```

---

## Workflow com Kanban Boards

### Configuração: kanban_boards.json

```json
{
  "boards": {
    "pipeline_orcamentos": {
      "title": "Pipeline de Orçamentos",
      "form": "orcamento_os",
      "columns": [
        {"tag": "pendente", "label": "Pendente", "color": "#6c757d"},
        {"tag": "enviado", "label": "Enviado ao Cliente", "color": "#17a2b8"},
        {"tag": "aprovado", "label": "Aprovado", "color": "#28a745"},
        {"tag": "os_gerada", "label": "OS Gerada", "color": "#20c997"}
      ]
    },
    "fluxo_amostras": {
      "title": "Fluxo de Amostras",
      "form": "entrada_amostra",
      "columns": [
        {"tag": "aguardando_coleta", "label": "Aguardando Coleta", "color": "#6c757d"},
        {"tag": "coletada", "label": "Coletada", "color": "#17a2b8"},
        {"tag": "recebida", "label": "Recebida", "color": "#007bff"},
        {"tag": "fracionada", "label": "Fracionada", "color": "#28a745"}
      ]
    },
    "execucao_analises": {
      "title": "Execução de Análises",
      "form": "analises_resultados",
      "columns": [
        {"tag": "aguardando", "label": "Aguardando", "color": "#6c757d"},
        {"tag": "em_execucao", "label": "Em Execução", "color": "#007bff"},
        {"tag": "concluida", "label": "Concluída", "color": "#28a745"}
      ]
    },
    "aprovacao_laudos": {
      "title": "Aprovação de Laudos",
      "form": "laudo",
      "columns": [
        {"tag": "rascunho", "label": "Rascunho", "color": "#6c757d"},
        {"tag": "revisao_rt", "label": "Revisão RT", "color": "#ffc107"},
        {"tag": "liberado", "label": "Liberado", "color": "#28a745"},
        {"tag": "entregue", "label": "Entregue", "color": "#20c997"}
      ]
    }
  }
}
```

---

## Fases de Implementação

### FASE 1: Entidades Base
**Complexidade:** Baixa | **Entidades:** 4

1. Criar specs: clientes, funcionarios, acreditadores, metodologias
2. Configurar persistence.json
3. Testar CRUD básico
4. Cadastrar dados de referência

### FASE 2: Hierarquia de Amostras
**Complexidade:** Média | **Entidades:** 3

1. Criar specs: classificacao_amostras, tipos_amostras, amostras_especificas
2. Implementar endpoints de search
3. Testar relacionamentos em cascata
4. Cadastrar taxonomia completa

### FASE 3: Catálogo de Análises
**Complexidade:** Média | **Entidades:** 4

1. Criar specs: analises, resultados_parciais, matriz_analises, precos_cliente
2. Testar autorelacionamento em análises
3. Configurar tabela de preços diferenciados
4. Validar cálculos de valores

### FASE 4: Fluxo Operacional
**Complexidade:** Alta | **Entidades:** 6

1. Criar specs: orcamento_os, coleta, entrada_amostra, fracionamento, analises_resultados, laudo
2. Implementar cadeia de custódia completa
3. Configurar Kanban boards
4. Testar fluxo end-to-end

### FASE 5: Testes e Validação
**Complexidade:** Alta

1. Executar testes de regressão
2. Criar massa de dados realista
3. Validar integridade referencial
4. Testar workflow completo
5. Documentar sistema

---

## Próximos Passos

1. **Limpar** dados e specs antigos do case
2. **Criar** specs JSON das entidades (17 arquivos)
3. **Configurar** persistence.json e kanban_boards.json
4. **Testar** cada fase antes de avançar
5. **Documentar** conforme implementação

---

**Versão:** 2.0
**Autor:** Claude Code + Arquiteto Agent
**Data:** 2025-12-26
