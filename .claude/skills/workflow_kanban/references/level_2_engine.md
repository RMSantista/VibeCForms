# Level 2: Engine
# Sistema Kanban-Workflow VibeCForms v4.0

**Nível de conhecimento**: Competent (Competente)
**Para quem**: Desenvolvedores implementando features core
**Conteúdo**: AutoTransitionEngine, AI Agents, PatternAnalyzer, fluxos completos de usuário

---

## Navegação

- **Anterior**: [Level 1 - Fundamentals](level_1_fundamentals.md)
- **Você está aqui**: Level 2 - Engine
- **Próximo**: [Level 3 - Interface](level_3_interface.md)
- **Outros níveis**: [Level 4](level_4_architecture.md) | [Level 5](level_5_implementation.md)

---

## Conteúdo Deste Nível

Este nível cobre a **engine central do sistema** - os mecanismos que fazem o workflow funcionar automaticamente:

- **Fluxos de usuário end-to-end**: Como usuários interagem com o sistema
- **Pattern Analysis**: Como a IA identifica padrões e anomalias
- **AI Agents**: Sistema de agentes inteligentes que sugerem transições
- **AutoTransitionEngine**: Engine que processa transições automáticas

---

## 4. AutoTransitionEngine Detalhado

### 4.1 Três Tipos de Transição

O sistema suporta **3 tipos de transição**:

```
+---------------------------------------------------------------+
|                     TIPOS DE TRANSIÇÃO                        |
+---------------------------------------------------------------+
|                                                               |
|  1. MANUAL (Usuário)                                          |
|     - Acionado por clique do usuário                          |
|     - Exige confirmação visual                                |
|     - Pode ter pré-requisitos (avisos)                        |
|     - Exemplo: "Aprovar Orçamento"                            |
|                                                               |
|  2. SYSTEM (Automática)                                       |
|     - Acionado automaticamente pelo sistema                   |
|     - Sem intervenção humana                                  |
|     - Baseado em condições ou timeouts                        |
|     - Exemplo: Auto-progressão após 2 horas                   |
|                                                               |
|  3. AGENT (IA)                                                |
|     - Sugerido por agente de IA                               |
|     - Requer aprovação do usuário                             |
|     - Baseado em análise de contexto                          |
|     - Exemplo: "IA sugere: Mover para Entrega"                |
|                                                               |
+---------------------------------------------------------------+
```

### 4.2 Cascade Progression (Progressão em Cascata)

Estados podem auto-progredir sequencialmente:

```
Estado A (auto_transition_to: B)
    |
    | (automático após 5 min)
    v
Estado B (auto_transition_to: C)
    |
    | (automático imediato)
    v
Estado C (auto_transition_to: D)
    |
    | (bloqueado - máximo 3 níveis)
    X

REGRA: Máximo 3 transições automáticas em cascata
       para evitar loops infinitos
```

**Exemplo prático:**

```json
{
  "states": [
    {
      "id": "novo",
      "auto_transition_to": "em_analise",
      "timeout_minutes": 5
    },
    {
      "id": "em_analise",
      "auto_transition_to": "processando",
      "timeout_minutes": 0
    },
    {
      "id": "processando",
      "auto_transition_to": "finalizado",
      "timeout_minutes": 0
    },
    {
      "id": "finalizado"
      // Não pode ter mais auto_transition (já são 3 níveis)
    }
  ]
}
```

### 4.3 Prerequisites por Estado (Não-bloqueantes)

**4 Tipos de Prerequisites:**

#### 4.3.1 field_check - Verificação de Campos

```json
{
  "type": "field_check",
  "field": "valor_total",
  "condition": "greater_than",
  "value": 1000,
  "message": "Valor deve ser maior que R$ 1000"
}
```

**Condições suportadas:**
- `equals`, `not_equals`
- `greater_than`, `less_than`, `greater_or_equal`, `less_or_equal`
- `contains`, `not_empty`, `is_true`, `is_false`

#### 4.3.2 external_api - Chamada a API Externa

```json
{
  "type": "external_api",
  "url": "https://api.example.com/validate/{process_id}",
  "method": "GET",
  "timeout_seconds": 5,
  "expected_status": 200,
  "message": "Validação externa pendente"
}
```

#### 4.3.3 time_elapsed - Tempo Decorrido

```json
{
  "type": "time_elapsed",
  "from": "created",
  "min_hours": 48,
  "message": "Aguarde 48 horas após criação"
}
```

**Opções de `from`:**
- `created` - Desde criação do processo
- `last_transition` - Desde última transição
- `specific_state` - Desde entrada em estado específico

#### 4.3.4 custom_script - Script Personalizado

```json
{
  "type": "custom_script",
  "script_path": "scripts/validate_pedido.py",
  "timeout_seconds": 30,
  "message": "Validação customizada pendente"
}
```

### 4.4 Auto-progression Logic

**Fluxo de auto-progressão:**

```
Processo entra em Estado X
         |
         v
AutoTransitionEngine.check_auto_progression(process_id)
         |
         v
Estado X tem auto_transition_to?
         |
         +---> NÃO: Para aqui
         |
         +---> SIM: Verifica prerequisites
                   |
                   +---> Todos OK?
                   |        SIM: Agenda transição
                   |        NÃO: Registra aviso, mas NÃO bloqueia
                   |
                   v
               Timeout configurado?
               |
               +---> timeout_minutes: 0 → Imediato
               +---> timeout_minutes: N → Agenda após N minutos
               |
               v
           Executa transição
               |
               v
           Incrementa cascade_count
               |
               v
           cascade_count < 3?
               |
               +---> SIM: Chama check_auto_progression() recursivamente
               +---> NÃO: Para aqui
```

### 4.5 Timeout Handlers

Estados podem ter **timeouts** que disparam ações automáticas:

```json
{
  "id": "aguardando_cliente",
  "timeout_hours": 72,
  "timeout_action": {
    "type": "transition",
    "target_state": "fechado_sem_resposta",
    "notification": {
      "email": true,
      "message": "Ticket fechado por timeout - sem resposta do cliente"
    }
  }
}
```

**Tipos de timeout_action:**
- `transition` - Move para outro estado
- `notification` - Envia notificação (email, SMS, webhook)
- `agent_intervention` - Aciona agente IA para análise
- `escalation` - Escala para gestor

### 4.6 Diagrama de Estados e Transições

```
+------------------------------------------------------------------+
|                     ESTADO E TRANSIÇÕES                          |
+------------------------------------------------------------------+

  [Estado A]
      |
      | (Manual) "Aprovar"
      | prerequisite: field_check(valor > 0)
      v
  [Estado B]
      |
      | (System) auto_transition_to: C
      | timeout_minutes: 60
      v
  [Estado C]
      |
      | (Agent) IA sugere baseado em análise
      | prerequisite: external_api(validation)
      v
  [Estado D]
      |
      | (Manual) "Finalizar"
      v
  [Estado Final]
```

---

## 5. Pattern Analysis por IA

### 5.1 PatternAnalyzer: Detecta Padrões de Transição

```python
class PatternAnalyzer:
    """
    Analisa histórico de transições para identificar padrões frequentes.

    Técnicas:
    - Frequent Pattern Mining (FP-Growth)
    - Sequential Pattern Analysis
    - Clustering de processos similares
    """

    def analyze_transition_patterns(
        self,
        kanban_id: str,
        min_support: float = 0.3
    ) -> list:
        """
        Identifica padrões frequentes de transições.

        Retorna padrões como:
        [
            {
                "pattern": ["orcamento", "pedido", "entrega", "concluido"],
                "support": 0.85,
                "avg_duration_hours": 72,
                "confidence": 0.92
            }
        ]
        """
```

**Exemplo de padrões identificados:**

```
PADRÃO COMUM (85% dos casos):
Orçamento → Pedido → Entrega → Concluído
Duração média: 72 horas

PADRÃO PROBLEMÁTICO (10% dos casos):
Orçamento → Pedido → Cancelado
Razão: Problemas de pagamento

PADRÃO EXCEPCIONAL (5% dos casos):
Orçamento → Concluído (pulo de etapas)
Razão: Pedidos urgentes VIP
```

### 5.2 AnomalyDetector: Identifica Transições Anômalas

```python
class AnomalyDetector:
    """
    Detecta processos com comportamento anômalo.

    Técnicas:
    - Isolation Forest (scikit-learn)
    - Statistical outlier detection
    - Duration-based anomalies
    """

    def detect_stuck_processes(
        self,
        kanban_id: str,
        threshold_hours: int = 48
    ) -> list:
        """
        Identifica processos travados em um estado.

        Retorna:
        [
            {
                "process_id": "proc_123",
                "current_state": "em_analise",
                "hours_stuck": 96,
                "expected_duration": 24,
                "anomaly_score": 0.95
            }
        ]
        """
```

### 5.3 Machine Learning para Análise de Histórico

**Modelos treinados:**

```
+---------------------------------------------------------------+
|                   ML MODELS PARA ANALYTICS                    |
+---------------------------------------------------------------+
|                                                               |
|  1. Duration Prediction Model                                |
|     - Input: Estado atual + dados do processo                |
|     - Output: Tempo estimado até conclusão                   |
|     - Algorithm: Gradient Boosting (XGBoost)                 |
|                                                               |
|  2. Risk Factor Identification                               |
|     - Input: Histórico de transições                         |
|     - Output: Probabilidade de cancelamento                  |
|     - Algorithm: Random Forest Classifier                    |
|                                                               |
|  3. Bottleneck Detection                                     |
|     - Input: Fluxo agregado de processos                     |
|     - Output: Estados com maior tempo médio                  |
|     - Algorithm: Statistical Analysis                        |
|                                                               |
+---------------------------------------------------------------+
```

### 5.4 Detecção de Bottlenecks e Otimizações

```python
class BottleneckAnalyzer:
    """
    Identifica gargalos no workflow.
    """

    def identify_bottlenecks(
        self,
        kanban_id: str,
        time_window_days: int = 30
    ) -> dict:
        """
        Retorna:
        {
            "bottleneck_state": "em_analise",
            "avg_duration_hours": 120,
            "expected_duration_hours": 24,
            "impact_score": 0.85,
            "affected_processes": 45,
            "recommendations": [
                "Adicionar mais revisores",
                "Automatizar verificação inicial",
                "Implementar priorização por urgência"
            ]
        }
        """
```

---

## 6. AI Agent System

### 6.1 BaseAgent: Classe Abstrata para Agentes

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Classe base para todos os agentes de IA do sistema.

    Agentes analisam contexto e sugerem transições inteligentes.
    """

    @abstractmethod
    def analyze_context(self, process_id: str) -> dict:
        """
        Analisa contexto do processo.

        Retorna informações relevantes para decisão.
        """

    @abstractmethod
    def suggest_transition(self, process_id: str) -> dict:
        """
        Sugere próxima transição baseado em análise.

        Retorna:
        {
            "suggested_state": "entrega",
            "confidence": 0.92,
            "justification": "Todos pré-requisitos satisfeitos...",
            "risk_factors": [],
            "estimated_duration": 24
        }
        """

    @abstractmethod
    def validate_transition(
        self,
        process_id: str,
        target_state: str
    ) -> dict:
        """
        Valida se transição proposta é segura.

        Retorna warnings/errors se houver riscos.
        """
```

### 6.2 Agentes Concretos por Estado

**Exemplo: OrcamentoAgent**

```python
class OrcamentoAgent(BaseAgent):
    """
    Agente especializado para estado 'orcamento'.

    Analisa:
    - Completude de dados do orçamento
    - Histórico de aprovação do cliente
    - Valor do pedido vs histórico
    - Prazo de resposta
    """

    def analyze_context(self, process_id: str) -> dict:
        process = self.repo.get_process(process_id)

        return {
            "data_completeness": self._check_required_fields(process),
            "client_approval_rate": self._get_client_history(process),
            "value_analysis": self._analyze_value(process),
            "response_time": self._calculate_response_time(process)
        }

    def suggest_transition(self, process_id: str) -> dict:
        context = self.analyze_context(process_id)

        if context["data_completeness"] < 0.8:
            return {
                "suggested_state": None,
                "confidence": 0.0,
                "justification": "Dados incompletos - aguardar preenchimento"
            }

        if context["client_approval_rate"] > 0.7:
            return {
                "suggested_state": "orcamento_aprovado",
                "confidence": 0.85,
                "justification": f"Cliente tem {context['client_approval_rate']*100}% de taxa de aprovação"
            }

        return {
            "suggested_state": None,
            "confidence": 0.5,
            "justification": "Aguardar resposta do cliente"
        }
```

### 6.3 Agent Orchestration System

```python
class AgentOrchestrator:
    """
    Coordena múltiplos agentes para análise completa.
    """

    def __init__(self):
        self.agents = {
            "orcamento": OrcamentoAgent(),
            "pedido": PedidoAgent(),
            "entrega": EntregaAgent(),
            "default": GenericAgent()
        }

    def get_agent_for_state(self, state_id: str) -> BaseAgent:
        """Retorna agente apropriado para o estado."""
        return self.agents.get(state_id, self.agents["default"])

    def run_analysis(self, process_id: str) -> dict:
        """
        Executa análise completa com agente apropriado.
        """
        process = self.repo.get_process(process_id)
        agent = self.get_agent_for_state(process["current_state"])

        context = agent.analyze_context(process_id)
        suggestion = agent.suggest_transition(process_id)

        return {
            "context": context,
            "suggestion": suggestion,
            "agent_used": agent.__class__.__name__
        }
```

### 6.4 Context Analysis

Agentes carregam **contexto rico** para análise:

```
CONTEXTO CARREGADO PARA DECISÃO:

1. Dados do Processo
   - Todos os campos do formulário origem
   - Metadados (criado_em, atualizado_em, etc.)

2. Histórico de Transições
   - Todas transições anteriores
   - Tempo em cada estado
   - Quem fez cada transição

3. Dados do Cliente/Entidade
   - Histórico de processos anteriores
   - Taxa de aprovação
   - Padrões de comportamento

4. Padrões do Kanban
   - Tempo médio por estado
   - Padrões mais comuns
   - Anomalias identificadas

5. Contexto Temporal
   - Hora do dia
   - Dia da semana
   - Sazonalidade
```

### 6.5 Intelligent Transition Suggestions

**UI de sugestão do agente:**

```
+---------------------------------------------------------------+
|  SUGESTÃO DE IA                                               |
+---------------------------------------------------------------+
|                                                               |
|  🤖 O agente de IA analisou este processo e sugere:           |
|                                                               |
|  ➡️  Mover para: ENTREGA                                      |
|  📊 Confiança: 92%                                            |
|                                                               |
|  Justificativa:                                               |
|  ✅ Todos pré-requisitos satisfeitos                          |
|  ✅ Pagamento confirmado                                      |
|  ✅ Estoque disponível                                        |
|  ⏱️ Tempo médio no estado atual: 24h (você: 22h)             |
|                                                               |
|  Fatores de risco: Nenhum                                    |
|                                                               |
|  [Aceitar Sugestão]  [Ignorar]  [Ver Detalhes]               |
|                                                               |
+---------------------------------------------------------------+
```

### 6.6 Justification System (Obrigatório para Agentes)

Todas sugestões de agentes **DEVEM** incluir justificativa:

```json
{
  "suggested_state": "entrega",
  "confidence": 0.92,
  "justification": "Análise indica alta probabilidade de sucesso na transição",
  "reasoning_steps": [
    "1. Verificado: campo 'pagamento_confirmado' = true",
    "2. Verificado: estoque disponível para produto #42",
    "3. Histórico: cliente tem 95% de taxa de conclusão",
    "4. Padrão: 87% dos processos similares progridem para entrega",
    "5. Tempo: processo está há 22h no estado atual (média: 24h)"
  ],
  "risk_factors": [],
  "alternative_suggestions": [
    {
      "state": "aguardando_estoque",
      "confidence": 0.15,
      "reason": "Se estoque não confirmado em 2h"
    }
  ]
}
```

---

## Próximos Passos

Após dominar a Engine, avance para:

**[Level 3 - Interface](level_3_interface.md)**: Visual Editor, Dashboard Analytics, Exports

---

**Referência original**: `VibeCForms/docs/planning/workflow/workflow_kanban_planejamento_v4_parte1.md` (Seções 4-7)
